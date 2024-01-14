from abc import ABC

from aiohttp.client import ClientSession

from swiftbots.all_types import ISoftClosable


class IAsyncHttpClientProvider(ISoftClosable, ABC):
    @property
    def _http_session(self) -> ClientSession:
        raise NotImplementedError()

    async def _ensure_http_session_created(self) -> None:
        raise NotImplementedError()

    async def _ensure_http_session_closed(self) -> None:
        raise NotImplementedError()
