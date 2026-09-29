"""A minimal in-process pub/sub for real-time updates via Server-Sent
Events: when one browser tab toggles a company's sponsorship status,
every other connected tab is told to refresh its own current search
rather than showing stale data until it happens to re-search itself."""

import asyncio
from typing import AsyncIterator, Awaitable, Callable

KEEP_ALIVE_TIMEOUT_SECONDS = 15


class Broadcaster:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._subscribers.discard(queue)

    async def publish(self, message: str) -> None:
        for queue in list(self._subscribers):
            await queue.put(message)


broadcaster = Broadcaster()


async def sse_event_stream(
    queue: asyncio.Queue,
    is_disconnected: Callable[[], Awaitable[bool]],
) -> AsyncIterator[str]:
    """The real SSE formatting/loop logic, decoupled from FastAPI's
    Request so it can be driven directly in a test (feed it a plain
    asyncio.Queue and a fake is_disconnected callable) instead of only
    being exercisable through a full, real streaming HTTP connection."""
    try:
        while True:
            if await is_disconnected():
                break
            try:
                message = await asyncio.wait_for(queue.get(), timeout=KEEP_ALIVE_TIMEOUT_SECONDS)
                yield f"event: refresh\ndata: {message}\n\n"
            except asyncio.TimeoutError:
                # A periodic comment line keeps the connection alive
                # through intermediate proxies/load balancers that would
                # otherwise time out an idle stream.
                yield ": keep-alive\n\n"
    finally:
        broadcaster.unsubscribe(queue)
