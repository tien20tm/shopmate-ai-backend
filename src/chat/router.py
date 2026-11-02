import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from src.chat.dependencies import (
    enforce_chat_rate_limit,
    hold_chat_slot,
    verify_request_checksum,
)
from src.chat.quota import (
    QuotaExceeded,
    reserve_chat_quota,
    seconds_until_next_day,
)
from src.chat.schemas import (
    ChatRequest,
    ChatResponse,
)
from src.chat.service import chat
from src.rate_limit import get_client_ip


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
    # Rate limit first, so rejected requests still use up the quota.
    dependencies=[
        Depends(enforce_chat_rate_limit),
        Depends(verify_request_checksum),
        Depends(hold_chat_slot),
    ],
)
async def ask_question(
    request: ChatRequest,
    http_request: Request,
):
    try:
        # Reserved here, after validation, so junk requests cannot burn the
        # daily quota for everyone else.
        exceeded = await reserve_chat_quota(get_client_ip(http_request))

        if exceeded is not None:
            raise HTTPException(
                429 if exceeded is QuotaExceeded.CLIENT else 503,
                "Daily chat limit reached",
                headers={"Retry-After": str(seconds_until_next_day())},
            )

        return await chat(
            message=request.message,
            session_id=request.session_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        # An unhandled 500 skips CORSMiddleware, so the browser would
        # only see a network error instead of this response.
        logger.exception("Chat agent failed")
        raise HTTPException(
            503,
            "Trợ lý AI tạm thời không phản hồi",
        ) from exc
