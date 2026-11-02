import asyncio

import pytest
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from src.chat import graph as graph_module
from src.chat.graph import recent_turns
from src.chat.service import chat
from src.config import settings


class FakeModel:
    # Stands in for ChatOpenAI, so these tests run the real graph offline.
    instances: list["FakeModel"] = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.calls = []
        FakeModel.instances.append(self)

    def bind_tools(self, tools):
        return self

    async def ainvoke(self, messages):
        self.calls.append(messages)
        return AIMessage(content=f"Trả lời {len(self.calls)}")


@pytest.fixture
def fake_model(monkeypatch):
    FakeModel.instances = []
    monkeypatch.setattr(graph_module, "ChatOpenAI", FakeModel)
    graph_module.get_agent_graph.cache_clear()
    yield FakeModel
    graph_module.get_agent_graph.cache_clear()


def ask(*messages, session_id="session-1"):
    async def main():
        return [
            await chat(message=message, session_id=session_id)
            for message in messages
        ]

    return asyncio.run(main())


def test_model_output_tokens_are_capped(fake_model):
    ask("Xin chào")

    assert (
        fake_model.instances[0].kwargs["max_tokens"]
        == settings.CHAT_MAX_OUTPUT_TOKENS
    )


def test_model_only_receives_recent_turns(fake_model, monkeypatch):
    monkeypatch.setattr(settings, "CHAT_HISTORY_TURNS", 2)

    ask("Câu 1", "Câu 2", "Câu 3", "Câu 4")

    sent = fake_model.instances[0].calls[-1]

    assert isinstance(sent[0], SystemMessage)
    assert [
        message.content
        for message in sent
        if isinstance(message, HumanMessage)
    ] == ["Câu 3", "Câu 4"]


def test_sessions_stay_separate(fake_model):
    ask("Câu của A", session_id="session-a")
    ask("Câu của B", session_id="session-b")

    sent = fake_model.instances[0].calls[-1]

    assert "Câu của A" not in [message.content for message in sent]


def test_recent_turns_keeps_short_history():
    messages = [HumanMessage(content="a"), AIMessage(content="b")]

    assert recent_turns(messages, 6) == messages


def test_recent_turns_keeps_tool_calls_with_their_results():
    call = AIMessage(
        content="",
        tool_calls=[{"name": "get_order_status", "args": {}, "id": "call-1"}],
    )
    result = ToolMessage(content="{}", tool_call_id="call-1")
    messages = [
        HumanMessage(content="cũ"),
        AIMessage(content="trả lời cũ"),
        HumanMessage(content="mới"),
        call,
        result,
        AIMessage(content="trả lời mới"),
    ]

    assert recent_turns(messages, 1) == messages[2:]
