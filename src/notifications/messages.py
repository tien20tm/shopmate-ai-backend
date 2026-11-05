import hashlib
import re
from datetime import datetime, timedelta, timezone


TEXT_PREVIEW_LENGTH = 300

VIETNAM_TIME = timezone(timedelta(hours=7))

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Nine or more digits, with optional separators: phone, ID and card numbers.
LONG_NUMBER_PATTERN = re.compile(r"(?<!\w)\+?\d(?:[\s.\-]?\d){8,}(?!\w)")


def mask_personal_data(text: str) -> str:
    text = EMAIL_PATTERN.sub("[đã ẩn email]", text)
    return LONG_NUMBER_PATTERN.sub("[đã ẩn số]", text)


def preview(text: str) -> str:
    # Mask first, so that truncating cannot leave part of a number unmasked.
    masked = " ".join(mask_personal_data(text).split())

    if len(masked) <= TEXT_PREVIEW_LENGTH:
        return masked

    return masked[:TEXT_PREVIEW_LENGTH].rstrip() + "…"


def client_code(client_ip: str) -> str:
    # Recognizes a returning visitor without putting the IP in the group.
    return hashlib.sha256(client_ip.encode("utf-8")).hexdigest()[:6]


def describe_device(user_agent: str) -> str:
    # Only fixed labels reach the message, never the raw header.
    browsers = (
        ("Edg/", "Edge"),
        ("OPR/", "Opera"),
        ("CocCoc", "Cốc Cốc"),
        ("Firefox/", "Firefox"),
        ("Chrome/", "Chrome"),
        ("Safari/", "Safari"),
    )
    systems = (
        ("Android", "Android"),
        ("iPhone", "iOS"),
        ("iPad", "iOS"),
        ("Windows", "Windows"),
        ("Mac OS", "macOS"),
        ("Linux", "Linux"),
    )

    browser = next(
        (name for token, name in browsers if token in user_agent),
        "Trình duyệt khác",
    )
    system = next(
        (name for token, name in systems if token in user_agent),
        "hệ điều hành khác",
    )

    return f"{browser} trên {system}"


def format_time(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    return now.astimezone(VIETNAM_TIME).strftime("%H:%M %d/%m/%Y")


def session_started_message(
    client_ip: str,
    path: str,
    referrer: str,
    user_agent: str,
) -> str:
    return "\n".join(
        [
            "🟢 Khách vào web",
            f"Khách: {client_code(client_ip)}",
            f"Trang: {path}, từ: {referrer or 'truy cập trực tiếp'}",
            f"Thiết bị: {describe_device(user_agent)}",
            f"Lúc: {format_time()}",
        ]
    )


def chat_message(
    client_ip: str,
    session_id: str,
    question: str,
    answer: str,
    tools_used: list[str],
    duration_seconds: float,
) -> str:
    return "\n".join(
        [
            "💬 Chat mới",
            f"Khách: {client_code(client_ip)}, phiên: {session_id[:8]}",
            f"Hỏi: {preview(question)}",
            f"Đáp: {preview(answer)}",
            f"Tool: {', '.join(tools_used) or 'không dùng'}",
            f"Thời gian xử lý: {duration_seconds:.1f}s",
            f"Lúc: {format_time()}",
        ]
    )


def chat_failed_message(
    client_ip: str,
    session_id: str,
    question: str,
    duration_seconds: float,
) -> str:
    return "\n".join(
        [
            "❌ Chat lỗi",
            f"Khách: {client_code(client_ip)}, phiên: {session_id[:8]}",
            f"Hỏi: {preview(question)}",
            f"Thời gian xử lý: {duration_seconds:.1f}s",
            f"Lúc: {format_time()}",
        ]
    )
