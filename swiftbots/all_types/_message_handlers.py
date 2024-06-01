"""
Message handlers do:
1. Modify message into context object according to `View`.Context interface.
2. Seek appropriate controller and its appropriate method, based on context.
3. Forward modified context to chosen controller method and execute.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from swiftbots.all_types import IContext, IController, ILogger, IView


class IMessageHandler(ABC):
    """
    Abstract class of Message Handler.
    About what message handlers do read swiftbots.all_types._message_handlers docstring.
    """

    @abstractmethod
    def __init__(self, controllers: List["IController"], logger: "ILogger"):
        raise NotImplementedError()

    @abstractmethod
    async def handle_message_async(self, view: "IView", context: "IContext") -> None:
        """Accept message and execute it in an appropriate controller"""
        raise NotImplementedError()


class IBasicMessageHandler(IMessageHandler, ABC):
    """
    Defines exactly one controller. Untouched context just
    will be processed in `default` method of the controller.
    """

    pass


class IChatMessageHandler(IMessageHandler, ABC):
    """
    Message handler is using for forwarding messages to appropriate controllers.
    This message handler perfectly works with ChatView context classes.

    If a command given, message handler will seek commands from controller
    and check if the message starts/match exactly like the command (case-insensitive).

    Pre context `message` field will be deleted.
    `raw` field will be added to a final context as a message duplicate.
    Also, `arguments` field will be added as a message with cut out command part.
    If command entirely match with the message, arguments will be empty string.

    Command must be at least one word.

    If no one commands match in controller, message handler will provide message to `default` method of the controller.
    Context fields `raw_message` and `arguments` will both contain not modified message.
    If `default` method is not given, it will be called `unknown_command_async` method of the view.
    If there are more than one `default` methods in controllers, any one can be used.
    """

    pass
