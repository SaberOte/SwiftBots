from abc import ABC
from typing import Callable

from swiftbots.types import ILogger, IView, IBasicView, IChatView, IMessageHandler


class BasicView(IBasicView, ABC):

    @IView._logger.getter
    def _logger(self) -> ILogger:
        return self.__logger

    @IView._logger.setter
    def _logger(self, logger: ILogger) -> None:
        self.__logger = logger

    @IView._listener.getter
    def _listener(self) -> Callable:
        return self.listen_async if self.__overriden_listener is None else self.__overriden_listener

    @IView._listener.setter
    def _listener(self, listener: Callable) -> None:
        assert isinstance(listener, Callable)
        self.__overriden_listener = listener


class ChatView(IChatView, BasicView, ABC):

    async def error_async(self, context: dict):
        """
        Inform user there is internal error.
        :param context: context with `sender` and `messages` fields
        """
        await self.send_async(self.error_message, context)

    async def unknown_command_async(self, context: dict):
        """
        If user sends some unknown shit, then needed say him about that
        :param context: context with `sender` and `messages` fields
        """
        self._logger.info(f'User sends unknown command. Context:\n{context}')
        await self.send_async(self.unknown_error_message, context)

    async def refuse_async(self, context: dict):
        """
        If user can't use it, then he must be aware.
        :param context: context with `sender` and `messages` fields
        """
        self._logger.info(f'Forbidden. Context:\n{context}')
        await self.send_async(self.refuse_message, context)


"""
class TelegramView(ChatView):
    pass


class VkontakteView(ChatView):
    pass
"""
