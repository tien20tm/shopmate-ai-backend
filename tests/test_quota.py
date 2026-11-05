import asyncio
from datetime import date, datetime, timezone
from urllib.parse import urlsplit

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.chat.models import ChatUsage
from src.chat.quota import (
    GLOBAL_SCOPE,
    QuotaExceeded,
    client_scope,
    reserve_chat_quota,
    seconds_until_next_day,
)
from src.config import settings


# A day far in the past, so these tests never touch today's real counters.
TEST_DAY = date(2000, 1, 1)

LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")


def run_with_db(scenario):
    # These tests write to the database, so they must never reach a remote one.
    if urlsplit(settings.DATABASE_URL).hostname not in LOCAL_HOSTS:
        pytest.skip("DATABASE_URL is not a local database")

    async def main():
        engine = create_async_engine(
            settings.DATABASE_URL,
            poolclass=NullPool,
        )
        factory = async_sessionmaker(engine, expire_on_commit=False)

        async def clean():
            async with factory() as db:
                await db.execute(
                    delete(ChatUsage).where(ChatUsage.day == TEST_DAY)
                )
                await db.commit()

        try:
            async with factory() as db:
                await db.execute(text("SELECT 1 FROM chat_usage LIMIT 1"))
        except OSError:
            pytest.skip("Local Postgres is not running")

        await clean()
        try:
            return await scenario(factory)
        finally:
            await clean()
            await engine.dispose()

    return asyncio.run(main())


async def read_count(factory, scope):
    async with factory() as db:
        return await db.scalar(
            select(ChatUsage.count).where(
                ChatUsage.day == TEST_DAY,
                ChatUsage.scope == scope,
            )
        )


@pytest.fixture
def limits(monkeypatch):
    def set_limits(total, per_ip):
        monkeypatch.setattr(settings, "CHAT_DAILY_LIMIT_TOTAL", total)
        monkeypatch.setattr(settings, "CHAT_DAILY_LIMIT_PER_IP", per_ip)

    return set_limits


def test_per_ip_limit_applies_to_each_ip_separately(limits):
    limits(total=100, per_ip=2)

    async def scenario(factory):
        reserve = lambda ip: reserve_chat_quota(ip, TEST_DAY, factory)

        assert await reserve("1.1.1.1") is None
        assert await reserve("1.1.1.1") is None
        assert await reserve("1.1.1.1") is QuotaExceeded.CLIENT
        assert await reserve("2.2.2.2") is None

        assert await read_count(factory, client_scope("1.1.1.1")) == 2
        assert await read_count(factory, GLOBAL_SCOPE) == 3

    run_with_db(scenario)


def test_total_limit_stops_many_different_ips(limits):
    limits(total=2, per_ip=100)

    async def scenario(factory):
        reserve = lambda ip: reserve_chat_quota(ip, TEST_DAY, factory)

        assert await reserve("1.1.1.1") is None
        assert await reserve("2.2.2.2") is None
        assert await reserve("3.3.3.3") is QuotaExceeded.TOTAL

        # The rejected request must not use up that IP's own quota.
        assert await read_count(factory, client_scope("3.3.3.3")) is None
        assert await read_count(factory, GLOBAL_SCOPE) == 2

    run_with_db(scenario)


def test_parallel_requests_cannot_pass_the_limit(limits):
    limits(total=5, per_ip=100)

    async def scenario(factory):
        results = await asyncio.gather(
            *(
                reserve_chat_quota(f"10.0.0.{index}", TEST_DAY, factory)
                for index in range(20)
            )
        )

        assert results.count(None) == 5
        assert results.count(QuotaExceeded.TOTAL) == 15
        assert await read_count(factory, GLOBAL_SCOPE) == 5

    run_with_db(scenario)


def test_zero_limit_blocks_everything(limits):
    limits(total=100, per_ip=0)

    async def scenario(factory):
        assert (
            await reserve_chat_quota("1.1.1.1", TEST_DAY, factory)
            is QuotaExceeded.CLIENT
        )
        assert await read_count(factory, GLOBAL_SCOPE) is None

    run_with_db(scenario)


def test_raw_ip_is_not_stored():
    assert "1.2.3.4" not in client_scope("1.2.3.4")


def test_seconds_until_next_day():
    now = datetime(2026, 11, 3, 23, 59, 30, tzinfo=timezone.utc)

    assert seconds_until_next_day(now) == 30
