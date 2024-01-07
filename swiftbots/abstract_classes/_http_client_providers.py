from abc import ABC

import aiohttp

from swiftbots.types import IAsyncHttpClientProvider, ISoftClosable


class AbstractAsyncHttpClientProvider(IAsyncHttpClientProvider, ISoftClosable, ABC):
    __http_session: aiohttp.client.ClientSession

    @property
    def http_session(self) -> aiohttp.client.ClientSession:
        return self.__http_session

    async def _soft_close_async(self) -> None:
        await self._ensure_http_session_closed()
        await super()._soft_close_async()

    async def _ensure_http_session_created(self) -> None:
        if '_http_session' not in vars(self):
            self.__http_session = aiohttp.ClientSession()

    async def _ensure_http_session_closed(self) -> None:
        if '_http_session' in vars(self) and not self._http_session.closed:
            await self._http_session.close()
