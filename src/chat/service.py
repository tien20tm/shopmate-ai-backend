
import json

from langchain_core.messages import (
    HumanMessage,
    ToolMessage,
)

from src.chat.context import AgentContext
from src.chat.graph import get_agent_graph
from src.config import settings


async def chat(
    message: str,
    session_id: str,
) -> dict:
    customer_id = settings.DEMO_CUSTOMER_ID

    graph = get_agent_graph()

    config = {
        "configurable": {
            "thread_id": (
                f"customer-{customer_id}:{session_id}"
            ),
        },
        "recursion_limit": 12,
    }

    result = await graph.ainvoke(
        {
            "messages": [
                HumanMessage(content=message)
            ]
        },
        config=config,
        context=AgentContext(
            customer_id=customer_id
        ),
    )

    messages = result["messages"]

    # Extract only messages created in the latest turn.
    last_user_index = max(
        i
        for i, msg in enumerate(messages)
        if isinstance(msg, HumanMessage)
    )

    turn_messages = messages[last_user_index + 1:]

    tools_used = []
    sources = []
    seen_sources = set()

    for msg in turn_messages:
        if not isinstance(msg, ToolMessage):
            continue

        if msg.name not in tools_used:
            tools_used.append(msg.name)

        if msg.name != "search_knowledge_base":
            continue

        data = json.loads(msg.content)

        for doc in data.get("documents", []):
            source_key = (
                doc["document_id"],
                doc["chunk_index"],
            )

            if source_key in seen_sources:
                continue

            seen_sources.add(source_key)

            sources.append({
                "document_id": doc["document_id"],
                "title": doc["title"],
                "chunk_index": doc["chunk_index"],
                "similarity": doc["similarity"],
            })

    return {
        "answer": str(messages[-1].content),
        "sources": sources,
        "tools_used": tools_used,
    }
