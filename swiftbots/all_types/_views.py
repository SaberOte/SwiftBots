import random
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, Optional, Type, Union

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from swiftbots.all_types import (
    IAsyncHttpClientProvider,
    IContext,
    IDatabaseConnectionProvider,
    ILoggerProvider,
    ISoftClosable,
)

if TYPE_CHECKING:
    from swiftbots.all_types import ILogger, IMessageHandler
    from swiftbots.bots import Bot


class IView(
    IDatabaseConnectionProvider,
    ILoggerProvider,
    IAsyncHttpClientProvider,
    ISoftClosable,
    ABC,
):
    """
    Abstract View class.
    Never inherit this class outside swiftbots module!
    """

    @property
    @abstractmethod
    def default_message_handler_class(self) -> Type["IMessageHandler"]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def associated_pre_context(self) -> Type["IContext"]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def associated_context(self) -> Type["IContext"]:
        raise NotImplementedError()

    @abstractmethod
    async def listen_async(self) -> AsyncGenerator["IContext", None]:
        """
        Input pipe for commands from outer resource.
        Method must use "yield" operator to return dict.
        Must be asynchronous.
        If view shouldn't listen to any outer resource, this method should run an endless async task.

        :return: Dict with additional information.
        Required fields described in derived types
        """
        yield IContext()  # Py Charm pisses off when the method doesn't return this
        raise NotImplementedError()

    @abstractmethod
    def init(
        self,
        bot: "Bot",
        logger: "ILogger",
        db_session_maker: Optional[async_sessionmaker[AsyncSession]],
    ) -> None:
        """
        Initialize the View
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def bot(self) -> "Bot":
        """Get the bot instance"""
        raise NotImplementedError()


class IBasicView(IView, ABC):
    """
    Minimal view must at least listen one outer resource and provide it to handle.
    """

    @abstractmethod
    async def listen_async(self) -> AsyncGenerator["IContext", None]:
        """
        Must yield dict with some information, that will be helpful when processing by controller.
        """
        yield IContext()  # Py Charm pisses off when the method doesn't return this
        raise NotImplementedError()


class IChatView(IView, ABC):
    """
    Generally, chat purposes view.
    Must LISTEN to many users and ANSWER them.
    Also, it must notify them about unexpected errors, unknown given commands or using of forbidden commands.
    """

    error_message = "Error occurred"
    unknown_error_message = "Unknown command"
    refuse_message = "Access forbidden"

    _admin: Any = None

    @abstractmethod
    async def listen_async(self) -> AsyncGenerator["IContext", None]:
        """
        For a ChatView listen_async must yield a Context with at least 2 fields: `sender` and `message`.
        `sender` needed for replying answer to a user.
        `message` needed for processing it by a message handler and forwarding to
        the appropriate controller and executing the appropriate command.
        """
        yield IContext()  # it's needed because PyCharm pisses off when there's no yield
        raise NotImplementedError()

    @abstractmethod
    async def send_async(
        self, message: str, user: Union[str, int], data: Optional[dict] = None
    ) -> dict:
        """
        Reply to the user from context.
        :param message: A message for a user.
        :param user: A user target to send a message
        :param data: Additional data for sending request
        """
        raise NotImplementedError()

    @abstractmethod
    async def reply_async(
        self, message: str, context: "IContext", data: Optional[dict] = None
    ) -> dict:
        """
        Reply to the user from context.
        :param message: A message for a user
        :param context: ChatView context
        :param data: additional data for sending request
        """
        raise NotImplementedError()

    @abstractmethod
    async def error_async(self, context: "IContext") -> dict:
        """
        Inform a user there is internal error.
        :param context: Context with `sender` and `messages` fields
        """
        raise NotImplementedError()

    @abstractmethod
    async def unknown_command_async(self, context: "IContext") -> dict:
        """
        If a user sends some unknown shit, then it's needed to say his about that.
        :param context: Context with `sender` and `messages` fields
        """
        raise NotImplementedError()

    @abstractmethod
    async def refuse_async(self, context: "IContext") -> dict:
        """
        If a user can't use it, then he must be aware.
        :param context: Context with `sender` and `messages` fields
        """
        raise NotImplementedError()

    @abstractmethod
    async def is_admin_async(self, user: Union[int, str]) -> bool:
        """
        Whether the user is an admin or not
        """
        raise NotImplementedError()


class ITelegramView(IChatView, ABC):
    @abstractmethod
    async def fetch_async(
        self,
        method: str,
        data: dict,
        headers: Optional[dict] = None,
        ignore_errors: bool = False,
    ) -> dict:
        """
        Custom send post request to telegram api.
        https://core.telegram.org/bots/api#available-methods
        """
        raise NotImplementedError()

    @abstractmethod
    async def update_message_async(
        self, text: str, message_id: int, context: "IContext", data: Optional[dict] = None
    ) -> dict:
        """
        Updating the message
        :param text: new message.
        :param message_id: message id
        :param context: context from user.
        :param data: additional data if needed.
        """
        raise NotImplementedError()

    @abstractmethod
    async def delete_message_async(
        self, message_id: int, context: "IContext", data: Optional[dict] = None
    ) -> dict:
        """
        Delete message `message_id`
        """
        raise NotImplementedError()

    @abstractmethod
    async def send_sticker_async(
        self, file_id: str, context: "IContext", data: Optional[dict] = None
    ) -> dict:
        """
        Send user a sticker with id `file_id`.
        Find out sticker file id: https://t.me/LeadConverterToolkitBot
        """
        raise NotImplementedError()


class IVkontakteView(IChatView, ABC):
    @abstractmethod
    async def fetch_async(
        self,
        method: str,
        data: Optional[dict] = None,
        headers: Optional[dict] = None,
        query_data: Optional[dict] = None,
        ignore_errors: bool = False,
    ) -> dict:
        """
        Send custom post request.
        https://dev.vk.com/ru/method
        """
        raise NotImplementedError()

    @abstractmethod
    async def update_message_async(
        self,
        message: str,
        message_id: int,
        context: "IContext",
        data: Optional[dict] = None,
    ) -> dict:
        """
        Updating the message
        :param message: new message.
        :param message_id: message id, which received from `response` field from send request.
        :param context: context from user.
        :param data: additional data if needed.
        """
        raise NotImplementedError()

    @abstractmethod
    async def send_sticker_async(
        self, sticker_id: int, context: "IContext", data: Optional[dict] = None
    ) -> dict:
        """
        Send a sticker to a user with id `sticker_id`.
        Find out sticker id: https://vk.com/id_stickera
        """
        raise NotImplementedError()

    @staticmethod
    def get_random_id() -> int:
        return random.randint(-(2**31), 2**31)
