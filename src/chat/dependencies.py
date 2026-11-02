import hashlib
import re
import time
from collections.abc import AsyncGenerator

from fastapi import Header, HTTPException, Request

from src.config import settings
from src.rate_limit import (
    SlidingWindowRateLimiter,
    enforce_rate_limit,
    get_client_ip,
)


# Milliseconds since the epoch, as produced by Date.now() in the frontend.
TIMESTAMP_PATTERN = re.compile(r"[0-9]{1,16}")

IN_FLIGHT_RETRY_AFTER_SECONDS = 5

chat_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.CHAT_RATE_LIMIT_REQUESTS,
    window_seconds=settings.CHAT_RATE_LIMIT_WINDOW_SECONDS,
)

chats_in_flight: set[str] = set()


async def enforce_chat_rate_limit(request: Request) -> None:
    enforce_rate_limit(chat_rate_limiter, request)


async def verify_request_checksum(
    request: Request,
    x_request_timestamp: str | None = Header(default=None),
    x_request_checksum: str | None = Header(default=None),
) -> None:
    # Detects altered bodies and limits replays to the allowed clock window.
    # It is not authentication: the frontend is public, so anyone can read
    # this format from the bundle and compute a valid checksum.
    if x_request_timestamp is None or x_request_checksum is None:
        raise HTTPException(400, "Missing request checksum headers")

    if not TIMESTAMP_PATTERN.fullmatch(x_request_timestamp):
        raise HTTPException(400, "Invalid request timestamp")

    age_ms = abs(time.time() * 1000 - int(x_request_timestamp))

    # Both directions: a future timestamp must not outlive the window.
    if age_ms > settings.CHAT_REQUEST_MAX_AGE_SECONDS * 1000:
        raise HTTPException(400, "Request timestamp out of range")

    signed = (
        await request.body()
        + f"!~~{x_request_timestamp}~~!".encode("utf-8")
    )

    if x_request_checksum.lower() != hashlib.sha256(signed).hexdigest():
        raise HTTPException(400, "Request checksum mismatch")


async def hold_chat_slot(request: Request) -> AsyncGenerator[None, None]:
    # One running chat per IP, so parallel requests cannot multiply the cost.
    client_ip = get_client_ip(request)

    if client_ip in chats_in_flight:
        raise HTTPException(
            429,
            "A chat request is already running",
            headers={"Retry-After": str(IN_FLIGHT_RETRY_AFTER_SECONDS)},
        )

    chats_in_flight.add(client_ip)
    try:
        yield
    finally:
        chats_in_flight.discard(client_ip)
