import hashlib
import math
from datetime import date, datetime, timedelta, timezone
from enum import Enum

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.chat.models import ChatUsage
from src.config import settings
from src.database import AsyncSessionLocal


GLOBAL_SCOPE = "global"


class QuotaExceeded(Enum):
    CLIENT = "client"
    TOTAL = "total"


def seconds_until_next_day(now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=1)).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    return math.ceil((tomorrow - now).total_seconds())


def client_scope(client_ip: str) -> str:
    digest = hashlib.sha256(client_ip.encode("utf-8")).hexdigest()
    return f"ip:{digest}"


async def _increment(
    db: AsyncSession,
    day: date,
    scope: str,
    limit: int,
) -> bool:
    if limit <= 0:
        return False

    # Atomic in the database, so parallel requests cannot pass the limit.
    statement = insert(ChatUsage).values(day=day, scope=scope, count=1)
    statement = statement.on_conflict_do_update(
        index_elements=[ChatUsage.day, ChatUsage.scope],
        set_={"count": ChatUsage.count + 1},
        where=ChatUsage.count < limit,
    ).returning(ChatUsage.count)

    result = await db.execute(statement)
    return result.first() is not None


async def reserve_chat_quota(
    client_ip: str,
    day: date | None = None,
    session_factory=AsyncSessionLocal,
) -> QuotaExceeded | None:
    # Stored in Postgres because in-memory counters would reset every time a
    # free host sleeps or restarts. Counts are not refunded when the agent
    # fails, since a failed run may already have spent tokens.
    day = day or datetime.now(timezone.utc).date()

    async with session_factory() as db:
        within_client_limit = await _increment(
            db,
            day,
            client_scope(client_ip),
            settings.CHAT_DAILY_LIMIT_PER_IP,
        )
        if not within_client_limit:
            await db.rollback()
            return QuotaExceeded.CLIENT

        within_total_limit = await _increment(
            db,
            day,
            GLOBAL_SCOPE,
            settings.CHAT_DAILY_LIMIT_TOTAL,
        )
        if not within_total_limit:
            await db.rollback()
            return QuotaExceeded.TOTAL

        await db.commit()

    return None
