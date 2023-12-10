from abc import ABC, abstractmethod
from typing import Callable, Optional

from swiftbots.types import ILogger, IBasicView, IChatView


class BasicView(IBasicView, ABC):

    def set_name(self, name: str) -> None:
        assert isinstance(name, str)
        self.__name = name

    def _get_name(self) -> str:
        """Return the name of the view"""
        if self.__name is None:
            return type(self).__name__
        else:
            return self.__name

    def _set_logger(self, logger: ILogger) -> None:
        self._logger = logger

    def _get_listener(self) -> Callable:
        """
        Listener waits updates from any outer resource like telegram and then returns it to handle.
        By default, method returns `alisten` method, which will be called to receive updates.
        If it's needed to override some behavior, you should use method _set_listener to set
        custom listener.
        :returns: method `alisten`
        """
        return self.listen_async if self.__overriden_listener is None else self.__overriden_listener

    def _set_listener(self, listener: Callable) -> None:
        """
        Override default listener (method `alisten`).
        Listener waits updates from any outer resource like telegram and then returns it to handle.
        Listener than will be used by message_handler, which can be overridden too in BotsApplication.
        :param listener: callable function, which will be called to receive updates.
        Must be asynchronous and use "yield" operator to return dict with
        information about outer resource command.
        """
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
