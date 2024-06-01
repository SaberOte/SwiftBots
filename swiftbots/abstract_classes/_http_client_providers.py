from abc import ABC
from typing import Optional

import aiohttp

from swiftbots.all_types import IAsyncHttpClientProvider, ISoftClosable


class AbstractAsyncHttpClientProvider(IAsyncHttpClientProvider, ISoftClosable, ABC):
    __http_session: Optional[aiohttp.client.ClientSession] = None

    @property
    def _http_session(self) -> aiohttp.client.ClientSession:
        if self.__http_session is None:
            raise AssertionError("No http session configured")
        elif self.__http_session.closed:
            raise AssertionError("Http session is already closed")
        return self.__http_session

    async def _soft_close_async(self) -> None:
        await self._ensure_http_session_closed()
        await super()._soft_close_async()

    async def _ensure_http_session_created(self) -> None:
        if self.__http_session is None:
            self.__http_session = aiohttp.ClientSession()

    async def _ensure_http_session_closed(self) -> None:
        if self.__http_session is not None and not self.__http_session.closed:
            await self.__http_session.close()
