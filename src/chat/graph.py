
from functools import lru_cache

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from langgraph.graph import (
    StateGraph,
    MessagesState,
    START,
)
from langgraph.prebuilt import (
    ToolNode,
    tools_condition,
)
from langgraph.checkpoint.memory import InMemorySaver

from src.config import settings
from src.chat.context import AgentContext
from src.chat.prompts import AGENT_SYSTEM_PROMPT
from src.chat.tools import (
    search_knowledge_base,
    get_order_status,
)


TOOLS = [
    search_knowledge_base,
    get_order_status,
]


@lru_cache(maxsize=1)
def get_agent_graph():
    # 1. Initialize LLM
    llm = ChatOpenAI(
        model=settings.OPENAI_CHAT_MODEL,
        temperature=0,
        timeout=30,
        max_retries=2,
        api_key=settings.OPENAI_API_KEY,
    )

    # 2. Bind tools
    model_with_tools = llm.bind_tools(TOOLS)

    # 3. Agent node
    async def agent_node(state: MessagesState):
        response = await model_with_tools.ainvoke(
            [
                SystemMessage(
                    content=AGENT_SYSTEM_PROMPT
                ),
                *state["messages"],
            ]
        )

        return {
            "messages": [response]
        }

    # 4. Define graph
    builder = StateGraph(
        MessagesState,
        context_schema=AgentContext,
    )

    builder.add_node(
        "agent",
        agent_node,
    )

    builder.add_node(
        "tools",
        ToolNode(TOOLS),
    )

    # 5. Define edges
    builder.add_edge(
        START,
        "agent",
    )

    builder.add_conditional_edges(
        "agent",
        tools_condition,
    )

    builder.add_edge(
        "tools",
        "agent",
    )

    # 6. Session memory
    checkpointer = InMemorySaver()

    return builder.compile(
        checkpointer=checkpointer,
    )
