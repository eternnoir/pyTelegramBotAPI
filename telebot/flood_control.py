import abc
import asyncio
import collections
import logging
import time

logger = logging.getLogger(__name__)


class AsyncRateLimiter:
    """
    Low-level rate limiter loosely based on https://github.com/RazerM/ratelimiter
    """

    def __init__(self, max_calls: int, period: float):
        self._call_times = collections.deque[float]()
        self._max_calls = max_calls
        self._period = period
        self._lock = asyncio.Lock()

    @property
    def timespan(self) -> float:
        return self._call_times[-1] - self._call_times[0]

    def delete_old_calls(self) -> None:
        oldest_to_keep = time.time() - self._period
        while self._call_times and self._call_times[0] < oldest_to_keep:
            self._call_times.popleft()

    @property
    def is_idle(self) -> bool:
        self.delete_old_calls()
        return len(self._call_times) > 0

    async def respect_rate_limit(self) -> None:
        async with self._lock:
            self.delete_old_calls()
            if len(self._call_times) >= self._max_calls:
                sleep_time = self._period - self.timespan
                if sleep_time > 0:
                    logger.debug(f"Sleeping for {sleep_time:.4f} sec to respect the rate limit...")
                    await asyncio.sleep(sleep_time)
            self._call_times.append(time.time())


class FloodControl(abc.ABC):
    @abc.abstractmethod
    async def respect(self, to_chat: int | str) -> None:
        """
        Blocks until it's safe to send a message to a given chat
        """
        ...


class NoFloodControl(FloodControl):
    async def respect(self, to_chat: int | str) -> None:
        pass


class TelegramBotApiFloodControl(FloodControl):
    """
    Telegram Bot API declares the following rate limits:
    - In a single chat, avoid sending more than one message per second
    - bots are not able to broadcast more than about 30 messages per second

    Details: https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this
    """

    def __init__(self, total_per_sec: int = 30, per_chat_per_sec: float = 1) -> None:
        self.bulk_limiter = AsyncRateLimiter(
            max_calls=total_per_sec,
            period=1.1,  # little more than a second for safety
        )
        self.per_chat_limiters: dict[str | int, AsyncRateLimiter] = dict()
        self.calls_per_chat_per_sec = per_chat_per_sec
        self._cleanup_task: asyncio.Task[None] | None = None

    async def _cleanup_limiters_after_delay(self) -> None:
        await asyncio.sleep(120)
        chats_to_delete = [chat for chat, limiter in self.per_chat_limiters.items() if limiter.is_idle]
        for chat in chats_to_delete:
            self.per_chat_limiters.pop(chat, None)

    async def respect(self, to_chat: int | str) -> None:
        if to_chat not in self.per_chat_limiters:
            self.per_chat_limiters[to_chat] = AsyncRateLimiter(
                # aiming for 4 messages per 5 seconds
                max_calls=int(4 * self.calls_per_chat_per_sec),
                period=5.0,
            )

        if len(self.per_chat_limiters) > 100 and (self._cleanup_task is None or self._cleanup_task.done()):
            self._cleanup_task = asyncio.create_task(self._cleanup_limiters_after_delay())

        per_chat_limiter = self.per_chat_limiters[to_chat]
        start_time = time.time()
        await per_chat_limiter.respect_rate_limit()
        await self.bulk_limiter.respect_rate_limit()
        wait_time = time.time() - start_time
        if wait_time > 0.01:
            logger.info(f"Waited for {wait_time:.3f} sec to respect Bot API flood control")


if __name__ == "__main__":
    import random

    async def main() -> None:
        # logging.basicConfig(level=logging.DEBUG)
        fc = TelegramBotApiFloodControl(total_per_sec=4)

        async def send(i: int) -> None:
            chat_id = i // 10
            await fc.respect(to_chat=chat_id)
            print(f"{chat_id}: sent at {time.time() - start_time:.3f} sec")

        await asyncio.sleep(random.random())
        start_time = time.time()
        await asyncio.gather(*(send(i) for i in range(100)))

    asyncio.run(main())
