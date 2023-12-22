from abc import ABC, abstractmethod
from typing import Callable, Optional, AsyncGenerator, TYPE_CHECKING

from swiftbots.message_handlers import BasicMessageHandler, ChatMessageHandler

if TYPE_CHECKING:
    from swiftbots.types import ILogger, IMessageHandler


class IContext(dict, ABC):
    """
    Abstract Context class.
    Dict inheritance allows to use the context like a regular dict,
    but provides a type hinting while using as a controller method argument type.
    """

    def __init__(self, **kwargs):
        """
        Constructor provides the interface of creating a Context like:
        `Context(message=message, sender=sender)`.
        """
        super().__init__()
        for attr in self.__annotations__:
            assert attr in kwargs, (f"Error while creating the Context object. Attribute {attr} must be provided in "
                                    f"a constructor like `Context({attr}={attr}...)")
        for arg_name in kwargs:
            self._add(arg_name, kwargs[arg_name])

    def _add(self, key: str, value: str):
        self[key] = value
        setattr(self, key, value)


class IView(ABC):
    """
    Abstract View class.
    Never inherit this class outside swiftbots module!
    """

    __logger: Optional['ILogger'] = None
    __overriden_listener: Optional[Callable] = None
    _default_message_handler_class: type['IMessageHandler']

    @abstractmethod
    def listen_async(self) -> AsyncGenerator['IView.Context', None]:
        """
        Input pipe for commands from outer resource.
        Method must use "yield" operator to return dict.
        Must be asynchronous.
        If view shouldn't listen any outer resource, this method should run endless async task.

        :return: dict with additional information. Required fields described in derived types
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def _logger(self) -> Optional['ILogger']:
        """Get logger of this view"""
        raise NotImplementedError()

    @_logger.setter
    @abstractmethod
    def _logger(self, logger: 'ILogger') -> None:
        """Set needed logger for this view"""
        raise NotImplementedError()

    @property
    @abstractmethod
    def _listener(self) -> Callable:
        """
        Listener waits updates from any outer resource like telegram and then returns it to handle.
        If it's needed to override some behavior, set _get_listener manually with custom one.
        :returns: listener function
        """
        raise NotImplementedError()

    @_listener.setter
    @abstractmethod
    def _listener(self, listener: Callable) -> None:
        """
        Override default listener.
        Listener waits updates from any outer resource like telegram and then returns it to handle.
        Listener than will be used by message_handler, which can be overridden too in BotsApplication.
        :param listener: callable function, which will be called to receive updates.
        Must be asynchronous and use "yield" operator to return dict with information about command.
        """
        raise NotImplementedError()

    class PreContext(IContext):
        """
        Declaration how pre context should look like
        when it yielded from view listener and starts
        processing in the message handler.
        """
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            raise NotImplementedError("Implement your own PreContext class in your View class")

    class Context(IContext):
        """
        Declaration how context should look like
        when it processed in message handler and
        forwarded to controller method.
        """
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            raise Exception("Implement your own Context class in your View class")


class IBasicView(IView, ABC):
    """
    Minimal view must at least listen one outer resource and provide it to handle.
    """

    _default_message_handler_class = BasicMessageHandler

    @abstractmethod
    def listen_async(self) -> AsyncGenerator['IBasicView.Context', None]:
        """
        Must yield dict with some information, that will be helpful when processing by controller.
        """
        raise NotImplementedError()

    class PreContext(IContext):
        """
        1 required attribute `message` of any type
        """
        __doc__ += IView.PreContext.__doc__
        message: object

    class Context(IContext):
        """
        1 required attribute `message` of any type
        """
        __doc__ += IView.Context.__doc__
        message: object


class IChatView(IView, ABC):
    """
    Generally, chat purposes view. Must LISTEN many users and ANSWER them.
    Also, must notify them about unexpected errors, unknown given commands or using of forbidden commands.
    """

    _default_message__default_message_handler_class = ChatMessageHandler

    error_message = 'Error occurred'
    unknown_error_message = 'Unknown command'
    refuse_message = 'Access forbidden'

    @abstractmethod
    def listen_async(self) -> AsyncGenerator['IChatView.Context', None]:
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

    class PreContext(IContext):
        """
        2 required fields:
        message - raw message from sender
        sender - user from who message was sent
        """
        __doc__ += IView.Context.__doc__

        message: str
        sender: str

        def __init__(self, message: str, sender: str, **kwargs):
            super().__init__(message=message, sender=sender, **kwargs)

    class Context(IContext):
        """
        3 required fields:
        raw - didn't modify message from sender
        arguments - additional message arguments after the command if given
        sender - user from who message was sent
        """
        __doc__ += IView.Context.__doc__
        raw: str
        arguments: str
        sender: str


"""
class TelegramView(ChatView):
    pass


class VkontakteView(ChatView):
    pass
"""
