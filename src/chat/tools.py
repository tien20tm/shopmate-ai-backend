
import json

from langchain.tools import tool, ToolRuntime

from src.chat.context import AgentContext
from src.database import AsyncSessionLocal
from src.orders.service import get_order
from src.knowledge.retriever import search_knowledge


@tool
async def search_knowledge_base(query: str) -> str:
    """Search ShopMate's FAQ and policies.

    Use this tool for questions about shipping, returns,
    refunds, warranty, payments, and order cancellation.

    Args:
        query: Search query describing the policy or FAQ.
    """
    documents = await search_knowledge(
        query=query,
        top_k=4,
    )

    return json.dumps(
        {"documents": documents},
        ensure_ascii=False,
    )


@tool
async def get_order_status(
    order_id: str,
    runtime: ToolRuntime[AgentContext],
) -> str:
    """Get the current customer's order information.

    Use this tool when the customer asks about a specific
    order's status, delivery, or cancellation eligibility.

    Args:
        order_id: Order ID, for example ORD-0001.
    """
    customer_id = runtime.context.customer_id

    async with AsyncSessionLocal() as db:
        order = await get_order(
            db=db,
            customer_id=customer_id,
            order_id=order_id,
        )

    if order is None:
        result = {
            "found": False,
            "message": "Order not found",
        }
    else:
        result = {
            "found": True,
            "order_id": order.id,
            "status": order.status,
            "created_at": order.created_at.isoformat(),
            "delivered_at": (
                order.delivered_at.isoformat()
                if order.delivered_at
                else None
            ),
        }

    return json.dumps(
        result,
        ensure_ascii=False,
    )
