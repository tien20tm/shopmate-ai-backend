import asyncio
import logging

import httpx

from src.config import settings


logger = logging.getLogger(__name__)

# httpx logs every URL at INFO level, and Bot API URLs contain the token.
logging.getLogger("httpx").setLevel(logging.WARNING)

QUEUE_SIZE = 100
# Telegram allows about 20 messages per minute in a group.
SECONDS_BETWEEN_MESSAGES = 4
REQUEST_TIMEOUT_SECONDS = 10
MAX_RETRY_AFTER_SECONDS = 60


class TelegramNotifier:
    def __init__(
        self,
        seconds_between_messages: float = SECONDS_BETWEEN_MESSAGES,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.seconds_between_messages = seconds_between_messages
        self.transport = transport
        self.queue: asyncio.Queue[str] = asyncio.Queue(maxsize=QUEUE_SIZE)
        self.dropped = 0
        self.worker: asyncio.Task | None = None

    @property
    def enabled(self) -> bool:
        return bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID)

    def notify(self, text: str, low_priority: bool = False) -> None:
        """Queue a message. Never blocks or raises, so callers cannot fail."""
        if not self.enabled:
            return

        # Keep room so a flood of low priority messages cannot crowd out chats.
        if low_priority and self.queue.qsize() >= QUEUE_SIZE // 2:
            self.dropped += 1
            return

        try:
            self.queue.put_nowait(text)
        except asyncio.QueueFull:
            self.dropped += 1

    async def start(self) -> None:
        if self.enabled and self.worker is None:
            self.worker = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self.worker is None:
            return

        self.worker.cancel()
        await asyncio.gather(self.worker, return_exceptions=True)
        self.worker = None

    async def _run(self) -> None:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT_SECONDS,
            transport=self.transport,
        ) as client:
            while True:
                text = await self.queue.get()
                await self._send(client, text)
                await asyncio.sleep(self.seconds_between_messages)

                if self.dropped:
                    dropped, self.dropped = self.dropped, 0
                    await self._send(
                        client,
                        f"⚠️ Đã bỏ qua {dropped} thông báo vì quá nhiều.",
                    )
                    await asyncio.sleep(self.seconds_between_messages)

    async def _send(self, client: httpx.AsyncClient, text: str) -> None:
        # Only exception types and status codes are logged, because httpx
        # errors can include the URL and therefore the bot token.
        try:
            response = await self._post(client, text)

            if response.status_code == 429:
                await asyncio.sleep(self._retry_after(response))
                response = await self._post(client, text)

            if not response.is_success:
                logger.warning(
                    "Telegram rejected a message: HTTP %s",
                    response.status_code,
                )
        except Exception as exc:
            logger.warning(
                "Could not reach Telegram: %s",
                type(exc).__name__,
            )

    async def _post(
        self,
        client: httpx.AsyncClient,
        text: str,
    ) -> httpx.Response:
        return await client.post(
            f"{settings.TELEGRAM_API_BASE_URL}"
            f"/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            # No parse_mode: visitors' text must not be able to add formatting
            # or disguised links to the message.
            json={
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": text,
                "disable_web_page_preview": True,
            },
        )

    def _retry_after(self, response: httpx.Response) -> float:
        try:
            seconds = response.json()["parameters"]["retry_after"]
            return min(float(seconds), MAX_RETRY_AFTER_SECONDS)
        except (ValueError, KeyError, TypeError):
            return self.seconds_between_messages


telegram_notifier = TelegramNotifier()
