import math
import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import HTTPException, Request

from src.config import settings


class SlidingWindowRateLimiter:
    # In-memory, so counts reset on restart and are per process. That fits
    # the single FastAPI process this MVP runs.
    def __init__(
        self,
        max_requests: int,
        window_seconds: int,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clock = clock
        self.hits: dict[str, deque[float]] = defaultdict(deque)
        self.last_sweep = clock()

    def hit(self, key: str) -> int | None:
        """Record a request. Returns seconds to wait if it is over the limit."""
        now = self.clock()
        self._sweep(now)

        hits = self.hits[key]
        self._drop_expired(hits, now)

        if len(hits) >= self.max_requests:
            oldest = hits[0] if hits else now
            return math.ceil(oldest + self.window_seconds - now)

        hits.append(now)
        return None

    def reset(self) -> None:
        self.hits.clear()

    def _drop_expired(self, hits: deque[float], now: float) -> None:
        while hits and hits[0] <= now - self.window_seconds:
            hits.popleft()

    def _sweep(self, now: float) -> None:
        # Forget idle IPs so the table cannot grow without bound.
        if now - self.last_sweep < self.window_seconds:
            return

        self.last_sweep = now
        for key in list(self.hits):
            self._drop_expired(self.hits[key], now)
            if not self.hits[key]:
                del self.hits[key]


def get_client_ip(request: Request) -> str:
    # request.client is the real peer. Behind a proxy, uvicorn fills it from
    # X-Forwarded-For only for proxies listed in FORWARDED_ALLOW_IPS, so a
    # client cannot dodge a limit by sending that header itself.
    return request.client.host if request.client else "unknown"


def enforce_rate_limit(
    limiter: SlidingWindowRateLimiter,
    request: Request,
) -> None:
    retry_after = limiter.hit(get_client_ip(request))

    if retry_after is not None:
        raise HTTPException(
            429,
            "Too many requests",
            headers={"Retry-After": str(retry_after)},
        )


read_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.READ_RATE_LIMIT_REQUESTS,
    window_seconds=settings.READ_RATE_LIMIT_WINDOW_SECONDS,
)


async def enforce_read_rate_limit(request: Request) -> None:
    enforce_rate_limit(read_rate_limiter, request)
