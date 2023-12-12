from abc import ABC, abstractmethod
from typing import Callable, Optional, AsyncGenerator, TYPE_CHECKING

if TYPE_CHECKING:
    from swiftbots.types import ILogger


class IView(ABC):
    """
    Abstract View class
    """

    _logger: Optional['ILogger'] = None
    __overriden_listener: Optional[Callable] = None


    @abstractmethod
    def listen_async(self) -> AsyncGenerator[dict, None]:
        """
        Input pipe for commands from outer resource.
        Method must use "yield" operator to return dict.
        Must be asynchronous.
        If view shouldn't listen any outer resource, this method should run endless async task.

        :return: dict with additional information. Required fields described in derived types
        """
        raise NotImplementedError()

    #
    # @abstractmethod
    # def commands_message_modifier(self, message: dict) -> dict:
    #     """
    #     The message from the view must be modified before sending it to a controller.
    #     This is method that determines how to turn `message` yielded from a view listener
    #     into `context` that used in controller methods
    #     """
    #     raise NotImplementedError()
    #
    # @abstractmethod
    # def default_modifier(self, message: dict) -> dict:
    #     """
    #     That message
    #     """

    @abstractmethod
    def _set_logger(self, logger: 'ILogger') -> None:
        """Set needed logger for this view"""
        raise NotImplementedError()

    @abstractmethod
    def _get_listener(self) -> Callable:
        """
        Listener waits updates from any outer resource like telegram and then returns it to handle.
        If it's needed to override some behavior, should use method _set_listener to set
        custom one.
        :returns: listener function
        """
        raise NotImplementedError()

    @abstractmethod
    def _set_listener(self, listener: Callable) -> None:
        """
        Override default listener.
        Listener waits updates from any outer resource like telegram and then returns it to handle.
        Listener than will be used by message_handler, which can be overridden too in BotsApplication.
        :param listener: callable function, which will be called to receive updates.
        Must be asynchronous and use "yield" operator to return dict with information about command.
        """
        raise NotImplementedError()


class IBasicView(IView, ABC):
    """
    Minimal view must at least listen one outer resource and provide it to handle.
    """

    @abstractmethod
    def listen_async(self) -> AsyncGenerator[dict, None]:
        """
        Must yield dict with some information, that will be helpful when processing by controller.
        """
        raise NotImplementedError()


class IChatView(IView, ABC):
    """
    Generally, chat purposes view. Must LISTEN many users and ANSWER them.
    Also, must notify them about unexpected errors, unknown given commands or using of forbidden commands.
    """

    error_message = 'Error occurred'
    unknown_error_message = 'Unknown command'
    refuse_message = 'Access forbidden'

    @abstractmethod
    def listen_async(self) -> AsyncGenerator[dict, None]:
        """
        For a ChatView listen_async must yield a dict with at least 2 fields: `sender` and `message`.
        `sender` needed for replying answer to a user.
        `message` needed for processing it by a message handler and forwarding to
        the appropriate controller and executing the appropriate command.
        """
        raise NotImplementedError()

    @abstractmethod
    async def send_async(self, message: str, context: dict) -> None:
        """
        Sending message to a user.
        :param message: a message for a user
        :param context: dict with a `sender` key
        """
        raise NotImplementedError()

    async def error_async(self, context: dict):
        """
        Inform a user there is internal error.
        :param context: context with `sender` and `messages` fields
        """
        raise NotImplementedError()

    async def unknown_command_async(self, context: dict):
        """
        If a user sends some unknown shit, then needed say him about that
        :param context: context with `sender` and `messages` fields
        """
        raise NotImplementedError()

    def refuse_async(self, context: dict):
        """
        If a user can't use it, then he must be aware.
        :param context: context with `sender` and `messages` fields
        """
        raise NotImplementedError()

    class Context(dict):
        message: str
        arguments: str
        sender: str

        def foo(self, key: str, value: str):
            self[key] = value
            setattr(self, key, value)


"""
class TelegramView(ChatView):
    pass


class VkontakteView(ChatView):
    pass
"""
