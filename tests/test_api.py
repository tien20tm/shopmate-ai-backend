import hashlib
import json
import time

import pytest
from fastapi.testclient import TestClient

from src.chat.dependencies import (
    chat_rate_limiter,
    chats_in_flight,
)
from src.chat.quota import QuotaExceeded
from src.main import app
from src.notifications.telegram import telegram_notifier
from src.rate_limit import (
    SlidingWindowRateLimiter,
    read_rate_limiter,
)
from src.sessions.router import (
    session_notice_limiter,
    session_rate_limiter,
)


client = TestClient(app)

ANSWER = {"answer": "Xin chào", "sources": [], "tools_used": []}


@pytest.fixture(autouse=True)
def reset_limits():
    chat_rate_limiter.reset()
    read_rate_limiter.reset()
    session_rate_limiter.reset()
    session_notice_limiter.reset()
    chats_in_flight.clear()


@pytest.fixture(autouse=True)
def notifications(monkeypatch):
    # Captures messages, so tests never reach Telegram even with a real token.
    sent = []

    def fake_notify(text, low_priority=False):
        sent.append({"text": text, "low_priority": low_priority})

    monkeypatch.setattr(telegram_notifier, "notify", fake_notify)
    return sent


@pytest.fixture(autouse=True)
def quota(monkeypatch):
    # The real SQL has its own tests in test_quota.py. Everything here runs
    # without touching the daily counters in the local database.
    state = {"result": None, "calls": 0}

    async def fake_reserve(client_ip):
        state["calls"] += 1
        return state["result"]

    monkeypatch.setattr("src.chat.router.reserve_chat_quota", fake_reserve)
    return state


def now_ms():
    return int(time.time() * 1000)


def sign(body: bytes, timestamp) -> str:
    signed = body + f"!~~{timestamp}~~!".encode("utf-8")
    return hashlib.sha256(signed).hexdigest()


def post_chat(
    message="Xin chào",
    session_id="test-session",
    timestamp=None,
    checksum=None,
    headers=None,
):
    body = json.dumps(
        {"session_id": session_id, "message": message},
        ensure_ascii=False,
    ).encode("utf-8")
    timestamp = now_ms() if timestamp is None else timestamp

    return client.post(
        "/api/v1/chat",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Request-Timestamp": str(timestamp),
            "X-Request-Checksum": checksum or sign(body, timestamp),
            **(headers or {}),
        },
    )


@pytest.fixture
def working_chat(monkeypatch):
    calls = []

    async def fake_chat(**kwargs):
        calls.append(kwargs)
        return ANSWER

    monkeypatch.setattr("src.chat.router.chat", fake_chat)
    return calls


def test_knowledge_list_uses_ingestion_document_ids():
    response = client.get("/api/v1/knowledge/documents")

    assert response.status_code == 200

    by_id = {doc["document_id"]: doc for doc in response.json()}
    doc = by_id["policies/return_policy"]

    assert doc["slug"] == "policies-return_policy"
    assert doc["doc_type"] == "policy"
    assert doc["title"] == "Chính sách đổi trả"
    assert doc["preview"]
    assert not doc["preview"].startswith("#")


def test_knowledge_detail_returns_markdown():
    response = client.get(
        "/api/v1/knowledge/documents/policies-return_policy"
    )

    assert response.status_code == 200
    assert response.json()["content"].startswith(
        "# Chính sách đổi trả"
    )


def test_knowledge_detail_unknown_slug_returns_404():
    response = client.get(
        "/api/v1/knowledge/documents/does-not-exist"
    )

    assert response.status_code == 404


def test_knowledge_detail_rejects_path_traversal():
    response = client.get(
        "/api/v1/knowledge/documents/..%2F..%2Fpyproject"
    )

    assert response.status_code == 404


def test_chat_failure_returns_503_with_cors_header(monkeypatch):
    async def failing_chat(**kwargs):
        raise RuntimeError("secret upstream detail")

    monkeypatch.setattr("src.chat.router.chat", failing_chat)

    response = post_chat(headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 503
    assert "secret" not in response.text
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:5173"
    )


def test_chat_accepts_valid_checksum(working_chat):
    response = post_chat(message="Đơn ORD-0002 hủy được không?")

    assert response.status_code == 200
    assert working_chat[0]["message"] == "Đơn ORD-0002 hủy được không?"


def test_chat_accepts_uppercase_checksum(working_chat):
    body = b'{"session_id": "s", "message": "hi"}'
    timestamp = now_ms()

    response = client.post(
        "/api/v1/chat",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Request-Timestamp": str(timestamp),
            "X-Request-Checksum": sign(body, timestamp).upper(),
        },
    )

    assert response.status_code == 200


def test_chat_rejects_missing_checksum(working_chat):
    response = client.post(
        "/api/v1/chat",
        json={"session_id": "test-session", "message": "Xin chào"},
    )

    assert response.status_code == 400
    assert working_chat == []


def test_chat_rejects_missing_timestamp(working_chat):
    body = b'{"session_id": "s", "message": "hi"}'

    response = client.post(
        "/api/v1/chat",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Request-Checksum": sign(body, now_ms()),
        },
    )

    assert response.status_code == 400
    assert working_chat == []


def test_chat_rejects_plain_body_hash(working_chat):
    body = b'{"session_id": "s", "message": "hi"}'

    response = client.post(
        "/api/v1/chat",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Request-Timestamp": str(now_ms()),
            "X-Request-Checksum": hashlib.sha256(body).hexdigest(),
        },
    )

    assert response.status_code == 400
    assert working_chat == []


@pytest.mark.parametrize(
    "offset_ms, expected",
    [
        (-61_000, 400),
        (61_000, 400),
        (-55_000, 200),
        (55_000, 200),
    ],
)
def test_chat_timestamp_window(working_chat, offset_ms, expected):
    # Correctly signed, so only the age decides the outcome.
    response = post_chat(timestamp=now_ms() + offset_ms)

    assert response.status_code == expected


@pytest.mark.parametrize(
    "timestamp",
    ["abc", "-1", "1.5", "9" * 5000],
)
def test_chat_rejects_malformed_timestamp(working_chat, timestamp):
    response = post_chat(timestamp=timestamp)

    assert response.status_code == 400
    assert working_chat == []


def test_chat_rejects_changed_timestamp(working_chat):
    # Replaying an old request with a fresh timestamp breaks the checksum.
    body = b'{"session_id": "s", "message": "hi"}'

    response = client.post(
        "/api/v1/chat",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Request-Timestamp": str(now_ms()),
            "X-Request-Checksum": sign(body, now_ms() - 120_000),
        },
    )

    assert response.status_code == 400
    assert working_chat == []


def test_chat_rejects_wrong_checksum(working_chat):
    response = post_chat(checksum="0" * 64)

    assert response.status_code == 400
    assert working_chat == []


def test_chat_validates_body_after_checksum(working_chat):
    response = post_chat(message="")

    assert response.status_code == 422
    assert working_chat == []


def test_chat_rate_limit_returns_429_with_retry_after(working_chat):
    limit = chat_rate_limiter.max_requests

    for _ in range(limit):
        assert post_chat().status_code == 200

    response = post_chat(headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 429
    assert 0 < int(response.headers["retry-after"]) <= 60
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:5173"
    )
    assert "retry-after" in response.headers[
        "access-control-expose-headers"
    ].lower()
    assert len(working_chat) == limit


def test_rejected_checksums_use_up_the_rate_limit(working_chat):
    for _ in range(chat_rate_limiter.max_requests):
        assert post_chat(checksum="0" * 64).status_code == 400

    assert post_chat(checksum="0" * 64).status_code == 429


def test_forwarded_header_cannot_dodge_the_rate_limit(working_chat):
    for index in range(chat_rate_limiter.max_requests):
        post_chat(headers={"X-Forwarded-For": f"10.0.0.{index}"})

    response = post_chat(headers={"X-Forwarded-For": "10.0.1.1"})

    assert response.status_code == 429


def make_limiter():
    now = [1000.0]
    limiter = SlidingWindowRateLimiter(
        max_requests=2,
        window_seconds=60,
        clock=lambda: now[0],
    )
    return limiter, now


def test_limiter_counts_each_ip_separately():
    limiter, _ = make_limiter()

    assert limiter.hit("1.1.1.1") is None
    assert limiter.hit("1.1.1.1") is None
    assert limiter.hit("1.1.1.1") == 60
    assert limiter.hit("2.2.2.2") is None


def test_limiter_window_slides():
    limiter, now = make_limiter()

    limiter.hit("ip")
    now[0] += 40
    limiter.hit("ip")
    now[0] += 19

    assert limiter.hit("ip") == 1

    now[0] += 1

    assert limiter.hit("ip") is None
    assert limiter.hit("ip") == 40


def test_limiter_forgets_idle_ips():
    limiter, now = make_limiter()

    limiter.hit("idle")
    now[0] += 61
    limiter.hit("active")

    assert list(limiter.hits) == ["active"]


def test_junk_requests_do_not_use_the_daily_quota(working_chat, quota):
    post_chat(checksum="0" * 64)
    post_chat(message="")
    post_chat(session_id="bad id!")

    assert quota["calls"] == 0

    assert post_chat().status_code == 200
    assert quota["calls"] == 1


def test_per_ip_daily_limit_returns_429_until_tomorrow(working_chat, quota):
    quota["result"] = QuotaExceeded.CLIENT

    response = post_chat(headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 429
    assert 0 < int(response.headers["retry-after"]) <= 86400
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:5173"
    )
    assert working_chat == []


def test_total_daily_limit_returns_503_with_retry_after(working_chat, quota):
    quota["result"] = QuotaExceeded.TOTAL

    response = post_chat()

    assert response.status_code == 503
    assert "retry-after" in response.headers
    assert working_chat == []


def test_quota_failure_never_calls_the_agent(working_chat, monkeypatch):
    async def broken_reserve(client_ip):
        raise RuntimeError("database down")

    monkeypatch.setattr("src.chat.router.reserve_chat_quota", broken_reserve)

    response = post_chat()

    assert response.status_code == 503
    assert "retry-after" not in response.headers
    assert working_chat == []


def test_second_chat_from_same_ip_is_rejected_while_one_runs(working_chat):
    chats_in_flight.add("testclient")

    response = post_chat()

    assert response.status_code == 429
    assert response.headers["retry-after"] == "5"
    assert working_chat == []


def test_chat_slot_is_released_after_success_and_failure(
    working_chat,
    monkeypatch,
):
    assert post_chat().status_code == 200
    assert chats_in_flight == set()

    async def failing_chat(**kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("src.chat.router.chat", failing_chat)

    assert post_chat().status_code == 503
    assert chats_in_flight == set()


@pytest.mark.parametrize("length, expected", [(500, 200), (501, 422)])
def test_chat_message_length_limit(working_chat, length, expected):
    assert post_chat(message="a" * length).status_code == expected


def test_read_endpoints_are_rate_limited(monkeypatch):
    monkeypatch.setattr(read_rate_limiter, "max_requests", 2)
    path = "/api/v1/knowledge/documents"

    assert client.get(path).status_code == 200
    assert client.get(path).status_code == 200

    response = client.get(path)

    assert response.status_code == 429
    assert "retry-after" in response.headers


def test_all_read_routers_share_the_rate_limit(monkeypatch):
    monkeypatch.setattr(read_rate_limiter, "max_requests", 0)

    for path in (
        "/api/v1/orders",
        "/api/v1/orders/ORD-0001",
        "/api/v1/products",
        "/api/v1/products/1",
        "/api/v1/knowledge/documents",
        "/api/v1/knowledge/documents/any",
    ):
        assert client.get(path).status_code == 429, path


def test_health_is_not_rate_limited(monkeypatch):
    monkeypatch.setattr(read_rate_limiter, "max_requests", 0)

    assert client.get("/health").status_code == 200


def post_session(payload=None, timestamp=None, checksum=None, headers=None):
    body = json.dumps(
        payload if payload is not None else {"path": "/orders"},
    ).encode("utf-8")
    timestamp = now_ms() if timestamp is None else timestamp

    return client.post(
        "/api/v1/session/start",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Request-Timestamp": str(timestamp),
            "X-Request-Checksum": checksum or sign(body, timestamp),
            **(headers or {}),
        },
    )


def test_session_start_sends_one_low_priority_message(notifications):
    response = post_session(
        {"path": "/orders", "referrer": "google.com"},
        headers={
            "User-Agent": "Mozilla/5.0 (Linux; Android 14) Chrome/130.0 Safari/537",
        },
    )

    assert response.status_code == 204
    assert response.content == b""
    assert len(notifications) == 1

    message = notifications[0]
    assert message["low_priority"] is True
    assert "testclient" not in message["text"]
    assert "/orders" in message["text"]
    assert "google.com" in message["text"]
    assert "Chrome trên Android" in message["text"]


def test_session_start_notifies_once_per_interval(notifications):
    assert post_session().status_code == 204
    assert post_session().status_code == 204
    assert post_session().status_code == 204

    assert len(notifications) == 1


def test_session_start_requires_valid_checksum(notifications):
    assert post_session(checksum="0" * 64).status_code == 400
    assert post_session(timestamp=now_ms() - 120_000).status_code == 400
    assert notifications == []


@pytest.mark.parametrize(
    "payload",
    [
        {"path": "orders"},
        {"path": "/a\nGiả mạo tin nhắn"},
        {"path": "/" + "a" * 200},
        {"path": "/orders", "referrer": "evil.com/\nGiả mạo"},
        {"referrer": "google.com"},
    ],
)
def test_session_start_rejects_bad_input(notifications, payload):
    assert post_session(payload).status_code == 422
    assert notifications == []


def test_session_start_is_rate_limited(notifications):
    for _ in range(session_rate_limiter.max_requests):
        assert post_session().status_code == 204

    response = post_session()

    assert response.status_code == 429
    assert "retry-after" in response.headers


def test_chat_success_sends_masked_message(working_chat, notifications):
    response = post_chat(
        message="Tôi là An, 0912 345 678, an@example.com, đơn ORD-0002",
    )

    assert response.status_code == 200
    assert len(notifications) == 1

    text = notifications[0]["text"]
    assert notifications[0]["low_priority"] is False
    assert "testclient" not in text
    assert "ORD-0002" in text
    assert "0912" not in text
    assert "an@example.com" not in text
    assert "Xin chào" in text


def test_chat_failure_sends_failure_message(monkeypatch, notifications):
    async def failing_chat(**kwargs):
        raise RuntimeError("secret upstream detail")

    monkeypatch.setattr("src.chat.router.chat", failing_chat)

    assert post_chat().status_code == 503
    assert len(notifications) == 1
    assert "Chat lỗi" in notifications[0]["text"]
    assert "secret" not in notifications[0]["text"]


def test_rejected_chats_send_no_message(working_chat, quota, notifications):
    post_chat(checksum="0" * 64)
    post_chat(message="")

    quota["result"] = QuotaExceeded.TOTAL
    post_chat()

    assert notifications == []
