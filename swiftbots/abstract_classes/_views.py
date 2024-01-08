import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import aiohttp

from swiftbots.all_types import IChatView, IContext

if TYPE_CHECKING:
    pass


class AbstractMessengerView(IChatView, ABC):
    __greeting_disabled = False

    def disable_greeting(self) -> None:
        self.__greeting_disabled = True

    async def listen_async(self) -> AsyncGenerator["IContext", None]:
        await self._ensure_http_session_created()

        while True:
            if not self.__greeting_disabled and self._admin is not None:
                await self.send_async(f"{self.bot.name} is started!", self._admin)

            try:
                async for update in self._get_updates_async():
                    pre_context = await self._deconstruct_message_async(update)
                    if pre_context:
                        yield pre_context

            except aiohttp.ServerConnectionError:
                await self._handle_server_connection_error_async()
            # except Exception as e:
            #     msg = 'Unhandled:' + '\nAnswer is:\n' + str(update) + '\n' + format_exc()
            #     self._logger.error(msg, update['message']['from']['id'])

    async def _handle_server_connection_error_async(self) -> None:
        await self.logger.info_async(
            f"Connection ERROR in {self.bot.name}. Sleep 5 seconds"
        )
        await asyncio.sleep(5)

    @abstractmethod
    async def _get_updates_async(self) -> AsyncGenerator[dict, None]:
        yield {}  # py charm pisses off without this
        raise NotImplementedError()

    @abstractmethod
    async def _deconstruct_message_async(self, update: dict) -> "IContext" | None:
        raise NotImplementedError()
