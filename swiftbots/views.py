from abc import ABC
from typing import Callable, TYPE_CHECKING

from swiftbots.types import ILogger, IView, IBasicView, IChatView, IMessageHandler
from swiftbots.message_handlers import BasicMessageHandler, ChatMessageHandler

if TYPE_CHECKING:
    from swiftbots.types import IBasicMessageHandler, IChatMessageHandler


class BasicView(IBasicView, ABC):

    _default_message_handler_class = BasicMessageHandler

    @property
    def _logger(self) -> ILogger:
        return self.__logger

    @_logger.setter
    def _logger(self, logger: ILogger) -> None:
        self.__logger = logger

    @property
    def _listener(self) -> Callable:
        return self.listen_async if self.__overriden_listener is None else self.__overriden_listener

    @_listener.setter
    def _listener(self, listener: Callable) -> None:
        assert isinstance(listener, Callable)
        self.__overriden_listener = listener


class ChatView(IChatView, BasicView, ABC):

    _default_message_handler_class = ChatMessageHandler

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
