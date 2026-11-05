from fastapi import APIRouter, Depends, Request, Response

from src.chat.dependencies import verify_request_checksum
from src.config import settings
from src.notifications.messages import session_started_message
from src.notifications.telegram import telegram_notifier
from src.rate_limit import (
    SlidingWindowRateLimiter,
    enforce_rate_limit,
    get_client_ip,
)
from src.sessions.schemas import SessionStartRequest


session_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.SESSION_RATE_LIMIT_REQUESTS,
    window_seconds=settings.SESSION_RATE_LIMIT_WINDOW_SECONDS,
)

# Allows one message per IP in each interval, so reopening tabs or calling this
# endpoint in a loop cannot flood the group.
session_notice_limiter = SlidingWindowRateLimiter(
    max_requests=1,
    window_seconds=settings.SESSION_NOTICE_INTERVAL_SECONDS,
)


async def enforce_session_rate_limit(request: Request) -> None:
    enforce_rate_limit(session_rate_limiter, request)


router = APIRouter(
    prefix="/api/v1/session",
    tags=["Session"],
)


@router.post(
    "/start",
    status_code=204,
    response_class=Response,
    dependencies=[
        Depends(enforce_session_rate_limit),
        Depends(verify_request_checksum),
    ],
)
async def start_session(
    body: SessionStartRequest,
    request: Request,
) -> None:
    client_ip = get_client_ip(request)

    if session_notice_limiter.hit(client_ip) is None:
        telegram_notifier.notify(
            session_started_message(
                client_ip=client_ip,
                path=body.path,
                referrer=body.referrer,
                user_agent=request.headers.get("user-agent", ""),
            ),
            low_priority=True,
        )
