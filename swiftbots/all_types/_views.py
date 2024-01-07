import random
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from swiftbots.all_types import IAsyncHttpClientProvider, IDatabaseConnectionProvider, ILoggerProvider, ISoftClosable

if TYPE_CHECKING:
    from swiftbots.bots import Bot
    from swiftbots.all_types import ILogger, IMessageHandler


class IContext(dict, ABC):
    """
    Abstract Context class.
    Dict inheritance allows using the context like a regular dict,
    but provides a type hinting while using as a controller method argument type.
    """

    def __init__(self, **kwargs):
        """
        Constructor provides the interface of creating a Context like:
        `Context(message=message, sender=sender)`.
        """
        super().__init__()
        if '__annotations__' in self:
            for attr in self.__annotations__:
                assert attr in kwargs, (f"Error while creating the Context object. Attribute {attr} must be provided "
                                        f"in a constructor like `Context({attr}={attr}...)")
        for arg_name in kwargs:
            self._add(arg_name, kwargs[arg_name])

    def _add(self, key: str, value: object) -> None:
        self[key] = value
        setattr(self, key, value)


class IView(IDatabaseConnectionProvider, ILoggerProvider, IAsyncHttpClientProvider, ISoftClosable, ABC):
    """
    Abstract View class.
    Never inherit this class outside swiftbots module!
    """

    default_message_handler_class: type['IMessageHandler']

    @abstractmethod
    async def listen_async(self) -> AsyncGenerator['IContext', None]:
        """
        Input pipe for commands from outer resource.
        Method must use "yield" operator to return dict.
        Must be asynchronous.
        If view shouldn't listen to any outer resource, this method should run an endless async task.

        :return: Dict with additional information.
        Required fields described in derived types
        """
        yield IContext()  # it's needed because PyCharm pisses off when there's no yield
        raise NotImplementedError()

    @abstractmethod
    def init(self, bot: 'Bot', logger: 'ILogger', db_session_maker: async_sessionmaker[AsyncSession] | None) -> None:
        """
        Initialize the View
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def bot(self) -> 'Bot':
        """Get the bot instance"""
        raise NotImplementedError()

    class PreContext(IContext, ABC):
        """
        Declaration how precontext should look like
        when it yielded from view listener and starts
        processing in the message handler.
        """
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            raise NotImplementedError("Implement your own PreContext class in your View class")

    class Context(IContext, ABC):
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

    @abstractmethod
    async def listen_async(self) -> AsyncGenerator['IContext', None]:
        """
        Must yield dict with some information, that will be helpful when processing by controller.
        """
        yield IContext()  # it's needed because PyCharm pisses off when there's no yield
        raise NotImplementedError()

    class PreContext(IContext):
        """
        1 required attribute `message` of any type
        """
        message: object

        def __init__(self, message: object, **kwargs):
            super().__init__(message=message, **kwargs)

    class Context(IContext):
        """
        1 required attribute `raw_message` of any type
        """
        raw_message: object


class IChatView(IView, ABC):
    """
    Generally, chat purposes view. Must LISTEN many users and ANSWER them.
    Also, must notify them about unexpected errors, unknown given commands or using of forbidden commands.
    """

    error_message = 'Error occurred'
    unknown_error_message = 'Unknown command'
    refuse_message = 'Access forbidden'

    _admin: Any = None

    @abstractmethod
    async def listen_async(self) -> AsyncGenerator['IContext', None]:
        """
        For a ChatView listen_async must yield a Context with at least 2 fields: `sender` and `message`.
        `sender` needed for replying answer to a user.
        `message` needed for processing it by a message handler and forwarding to
        the appropriate controller and executing the appropriate command.
        """
        yield IContext()  # it's needed because PyCharm pisses off when there's no yield
        raise NotImplementedError()

    @abstractmethod
    async def send_async(self, message: str, user: str | int, data: dict | None = None) -> dict:
        """
        Reply to the user from context.
        :param message: A message for a user.
        :param user: A user target to send a message
        :param data: Additional data for sending request
        """
        raise NotImplementedError()

    @abstractmethod
    async def reply_async(self, message: str, context: 'IContext', data: dict | None = None) -> dict:
        """
        Reply to the user from context.
        :param message: A message for a user
        :param context: ChatView context
        :param data: additional data for sending request
        """
        raise NotImplementedError()

    @abstractmethod
    async def error_async(self, context: 'IContext') -> dict:
        """
        Inform a user there is internal error.
        :param context: Context with `sender` and `messages` fields
        """
        raise NotImplementedError()

    @abstractmethod
    async def unknown_command_async(self, context: 'IContext') -> dict:
        """
        If a user sends some unknown shit, then it's needed to say his about that.
        :param context: Context with `sender` and `messages` fields
        """
        raise NotImplementedError()

    @abstractmethod
    async def refuse_async(self, context: 'IContext') -> dict:
        """
        If a user can't use it, then he must be aware.
        :param context: Context with `sender` and `messages` fields
        """
        raise NotImplementedError()

    @abstractmethod
    async def is_admin_async(self, user: int | str) -> bool:
        """
        Whether the user is an admin or not
        """
        raise NotImplementedError()

    class PreContext(IContext):
        """
        1 require field:
        message - raw message from sender.
        1 optional but mostly useful field:
        sender - user from who message was sent
        """
        message: str
        sender: str

        def __init__(self, message: str, sender: str = 'unknown', **kwargs):
            super().__init__(message=message, sender=sender, **kwargs)

    class Context(IContext):
        """
        4 required fields:
        raw_message - not modified message.
        arguments - message with cut out command part (empty string if not given).
        command - part of the message what was matched as a command.
        sender - user from who message was received.

        If default method was called, raw_message, command and arguments will both contain not modified message.
        """
        raw_message: str
        arguments: str
        command: str
        sender: str


class ITelegramView(IChatView, ABC):

    @abstractmethod
    async def fetch_async(self, method: str, data: dict, ignore_errors: bool = False) -> dict | None:
        """
        Custom send post request to telegram api.
        https://core.telegram.org/bots/api#available-methods
        """
        raise NotImplementedError()

    @abstractmethod
    async def update_message_async(self, text: str, message_id: int, context: 'IContext', data: dict | None = None) -> dict:
        """
        Updating the message
        :param text: new message.
        :param message_id: message id
        :param context: context from user.
        :param data: additional data if needed.
        """
        raise NotImplementedError()

    @abstractmethod
    async def delete_message_async(self, message_id: int, context: 'IContext', data: dict | None = None) -> dict:
        """
        Delete message `message_id`
        """
        raise NotImplementedError()

    @abstractmethod
    async def send_sticker_async(self, file_id: str, context: 'IContext', data: dict | None = None) -> dict:
        """
        Send user a sticker with id `file_id`.
        Find out sticker file id: https://t.me/LeadConverterToolkitBot
        """
        raise NotImplementedError()

    class PreContext(IContext):
        """
        Three required fields:
        message - raw message from sender.
        sender - user from who message was received
        username - user's symbolic username: `no username` if user has no symbolic username
        """
        message: str
        sender: str
        username: str

        def __init__(self, message: str, sender: str, username: str, **kwargs):
            super().__init__(message=message, sender=sender, username=username, **kwargs)

    class Context(IContext):
        """
        Five required fields:
        raw_message - not modified message.
        arguments - message with cut out command part (empty string if not given).
        command - part of the message what was matched as a command.
        sender - user from who message was received.
        username - user's symbolic username. `no username` if user has no symbolic username

        If default method was called, raw_message, command and arguments will both contain not modified message.
        """
        raw_message: str
        arguments: str
        command: str
        sender: str
        username: str


class IVkontakteView(IChatView, ABC):

    @abstractmethod
    async def fetch_async(self, method: str, data: dict | None= None,
                          headers: dict | None = None, query_data: dict | None = None,
                          ignore_errors: bool = False) -> dict:
        """
        Send custom post request.
        https://dev.vk.com/ru/method
        """
        raise NotImplementedError()

    @abstractmethod
    async def update_message_async(self, message: str, message_id: int, context: 'IContext', data: dict | None = None) -> dict:
        """
        Updating the message
        :param message: new message.
        :param message_id: message id, which received from `response` field from send request.
        :param context: context from user.
        :param data: additional data if needed.
        """
        raise NotImplementedError()

    @abstractmethod
    async def send_sticker_async(self, sticker_id: int, context: 'IContext', data: dict | None = None) -> dict:
        """
        Send a sticker to a user with id `sticker_id`.
        Find out sticker id: https://vk.com/id_stickera
        """
        raise NotImplementedError()

    @staticmethod
    def get_random_id() -> int:
        return random.randint(-2 ** 31, 2 ** 31)

    class PreContext(IContext):
        """
        3 required fields:
        message - raw message from sender.
        sender - user from who message was received
        message_id - identified of message
        """
        message: str
        sender: int
        message_id: int

        def __init__(self, message: str, sender: int, message_id: int, **kwargs):
            super().__init__(message=message, sender=sender, message_id=message_id, **kwargs)

    class Context(IContext):
        """
        5 required fields:
        raw_message - not modified message.
        arguments - message with cut out command part (empty string if not given).
        command - part of the message what was matched as a command.
        sender - user from who message was received.
        message_id - message id

        If default method was called, raw_message, command and arguments will both contain not modified message.
        """
        raw_message: str
        arguments: str
        command: str
        sender: int
        message_id: int
