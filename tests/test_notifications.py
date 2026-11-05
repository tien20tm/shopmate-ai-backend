import asyncio
import json
import logging
from datetime import datetime, timezone

import httpx
import pytest

from src.config import settings
from src.notifications.messages import (
    chat_message,
    client_code,
    describe_device,
    format_time,
    mask_personal_data,
    preview,
)
from src.notifications.telegram import QUEUE_SIZE, TelegramNotifier


TOKEN = "123456:SECRET-TOKEN"


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", TOKEN)
    monkeypatch.setattr(settings, "TELEGRAM_CHAT_ID", "-100123")


def make_notifier(handler):
    return TelegramNotifier(
        seconds_between_messages=0,
        transport=httpx.MockTransport(handler),
    )


async def drain(notifier, expected, sent):
    await notifier.start()
    for _ in range(200):
        if len(sent) >= expected and notifier.queue.empty():
            break
        await asyncio.sleep(0.01)
    await asyncio.sleep(0.01)
    await notifier.stop()


@pytest.mark.parametrize(
    "text",
    [
        "0912345678",
        "0912 345 678",
        "0912.345.678",
        "091-234-5678",
        "+84912345678",
        "+84 912 345 678",
        "CCCD 012345678901",
    ],
)
def test_masks_phone_and_id_numbers(text):
    masked = mask_personal_data(text)

    assert "[đã ẩn số]" in masked
    assert "345" not in masked


def test_masks_email():
    assert mask_personal_data("Mail a.b+c@mail.example.vn nhé") == (
        "Mail [đã ẩn email] nhé"
    )


@pytest.mark.parametrize(
    "text",
    ["Đơn ORD-0002", "Giá 1.605.000 ₫", "SKU-007", "trong 7 ngày"],
)
def test_keeps_order_codes_and_prices(text):
    assert mask_personal_data(text) == text


def test_preview_masks_before_cutting():
    # The number straddles the cut, so cutting first would leak its start.
    text = "a" * 295 + " 0912345678"

    assert "0912" not in preview(text)


def test_preview_cuts_long_text_and_flattens_lines():
    result = preview("dòng 1\ndòng 2 " + "x" * 400)

    assert "\n" not in result
    assert len(result) == 301
    assert result.endswith("…")


def test_client_code_is_stable_and_hides_the_ip():
    code = client_code("113.161.1.2")

    assert len(code) == 6
    assert client_code("113.161.1.2") == code
    assert client_code("113.161.1.3") != code


@pytest.mark.parametrize(
    "user_agent, expected",
    [
        (
            "Mozilla/5.0 (Windows NT 10.0) Chrome/130.0 Safari/537 Edg/130.0",
            "Edge trên Windows",
        ),
        (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17) Version/17 Safari/605",
            "Safari trên iOS",
        ),
        ("", "Trình duyệt khác trên hệ điều hành khác"),
        ("<script>evil</script>", "Trình duyệt khác trên hệ điều hành khác"),
    ],
)
def test_describe_device_uses_fixed_labels(user_agent, expected):
    assert describe_device(user_agent) == expected


def test_time_is_shown_in_vietnam_time():
    now = datetime(2026, 11, 6, 20, 30, tzinfo=timezone.utc)

    assert format_time(now) == "03:30 07/11/2026"


def test_full_chat_message_fits_telegram_limit():
    text = chat_message(
        "2001:db8::1",
        "s" * 64,
        "q" * 500,
        "a" * 5000,
        ["search_knowledge_base", "get_order_status"],
        1.5,
    )

    assert len(text) < 4096


def test_sends_plain_text_to_the_configured_group(configured):
    sent = []

    def handler(request):
        sent.append(request)
        return httpx.Response(200, json={"ok": True})

    async def main():
        notifier = make_notifier(handler)
        notifier.notify("<b>Xin chào</b>")
        await drain(notifier, 1, sent)

    asyncio.run(main())

    assert len(sent) == 1
    assert sent[0].url.path == f"/bot{TOKEN}/sendMessage"

    body = json.loads(sent[0].content)
    assert body["chat_id"] == "-100123"
    assert body["text"] == "<b>Xin chào</b>"
    assert "parse_mode" not in body


def test_is_disabled_without_configuration(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setattr(settings, "TELEGRAM_CHAT_ID", "-100123")

    async def main():
        notifier = make_notifier(lambda request: httpx.Response(200))
        notifier.notify("tin")
        await notifier.start()

        assert notifier.queue.empty()
        assert notifier.worker is None

    asyncio.run(main())


def test_worker_survives_errors_and_never_logs_the_token(configured, caplog):
    sent = []

    def handler(request):
        sent.append(request)
        if len(sent) == 1:
            raise httpx.ConnectError(f"cannot reach {request.url}")
        if len(sent) == 2:
            return httpx.Response(500)
        return httpx.Response(200, json={"ok": True})

    async def main():
        notifier = make_notifier(handler)
        notifier.notify("một")
        notifier.notify("hai")
        notifier.notify("ba")
        await drain(notifier, 3, sent)

    with caplog.at_level(logging.DEBUG):
        asyncio.run(main())

    assert len(sent) == 3
    assert "SECRET-TOKEN" not in caplog.text


def test_retries_once_after_telegram_rate_limit(configured):
    sent = []

    def handler(request):
        sent.append(request)
        if len(sent) == 1:
            return httpx.Response(
                429,
                json={"parameters": {"retry_after": 0}},
            )
        return httpx.Response(200, json={"ok": True})

    async def main():
        notifier = make_notifier(handler)
        notifier.notify("tin")
        await drain(notifier, 2, sent)

    asyncio.run(main())

    assert len(sent) == 2


def test_full_queue_drops_and_reports_without_raising(configured):
    sent = []

    def handler(request):
        sent.append(json.loads(request.content)["text"])
        return httpx.Response(200, json={"ok": True})

    async def main():
        notifier = make_notifier(handler)

        for index in range(QUEUE_SIZE + 3):
            notifier.notify(f"chat {index}")

        assert notifier.dropped == 3

        await drain(notifier, QUEUE_SIZE + 1, sent)

    asyncio.run(main())

    assert any("Đã bỏ qua 3 thông báo" in text for text in sent)


def test_low_priority_keeps_room_for_chats(configured):
    async def main():
        notifier = make_notifier(lambda request: httpx.Response(200))

        for index in range(QUEUE_SIZE):
            notifier.notify(f"khách {index}", low_priority=True)

        assert notifier.queue.qsize() == QUEUE_SIZE // 2

        notifier.notify("chat")

        assert notifier.queue.qsize() == QUEUE_SIZE // 2 + 1

    asyncio.run(main())
