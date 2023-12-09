from abc import ABC, abstractmethod
from swiftbots.types import LoggerInterface


class View(ABC):
    """
    Minimal view must at least listen some outer resource and invoke bot controllers
    """

    _logger: LoggerInterface

    @abstractmethod
    async def alisten(self) -> dict:
        """
        Input pipe for commands from user.
        Method must use "yield" operator to give information and command.
        Must be asynchronous
        """
        raise NotImplementedError(f"Not implemented method `listen` in {self._get_name()}")

    def _get_name(self) -> str:
        """Returns the name of the view"""
        return type(self).__name__

    def _set_logger(self, logger: LoggerInterface) -> None:
        self._logger = logger


class ChatView(View):
    """
    General chat purposes view. Must LISTEN many users and ANSWER them
    """

    error_message = 'Error occurred'
    unknown_error_message = 'Unknown command'
    refuse_message = 'Access forbidden'

    @abstractmethod
    async def asend(self, message: str, context: dict) -> None:
        """
        Sending message to user.
        :param message: the message for user
        :param context: context with `sender` and `messages` fields
        """
        raise NotImplementedError(f"Not implemented method `send` in {self._get_name()}")

    @abstractmethod
    async def alisten(self) -> dict:
        """
        Input pipe for commands from user.
        Method must use "yield" operator to give information and command.
        Must be asynchronous
        :returns: dictionary with `sender` and `messages` fields. There may be more fields
        """
        raise NotImplementedError(f"Not implemented method `listen` in {self._get_name()}")

    async def aerror(self, context: dict):
        """
        Inform user there is internal error.
        :param context: context with `sender` and `messages` fields
        """
        await self.asend(self.error_message, context)

    async def aunknown_command(self, context: dict):
        """
        If user sends some unknown shit, then needed say him about that
        :param context: context with `sender` and `messages` fields
        """
        self._logger.log(f'User sends unknown command. Context:\n{context}')
        return await self.asend(self.unknown_error_message, context)

    def refuse(self, context: dict):
        """
        If user can't use it, then he must be aware.
        :param context: context with `sender` and `messages` fields
        """
        self._logger.log(f'Forbidden. Context:\n{context}')
        return self.asend(self.refuse_message, context)


"""
class TelegramView(ChatView):
    pass


class VkontakteView(ChatView):
    pass
"""
