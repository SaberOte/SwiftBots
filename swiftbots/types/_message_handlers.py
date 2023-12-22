"""
Message handlers do:
1. Modify message into context object according to `View`.Context interface.
2. Seek appropriate controller and its appropriate method, based on context.
3. Forward modified context to chosen controller method and execute.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiftbots.types import IView, IController, ILogger, IContext


class MessageHandlingResult(Enum):
    SUCCESS = 1
    ERROR = 2
    DEFAULT_HANDLER_INVOKED = 3
    NO_MATCHES = 4


class IMessageHandler(ABC):
    """
    Abstract class of Message Handler.
    About what message handlers do read swiftbots.types._message_handlers docstring.
    """

    @abstractmethod
    def __init__(self, controllers: list['IController'], logger: 'ILogger'):
        raise NotImplementedError()

    @abstractmethod
    async def handle_message_async(self, view: 'IView', context: 'IContext'):
        """Accept message and execute it in appropriate controller"""
        raise NotImplementedError()


class IBasicMessageHandler(IMessageHandler, ABC):
    """
    Defines exactly one controller. Untouched message just
    will be processed in `default` method of it.
    """
    pass


class IChatMessageHandler(IMessageHandler, ABC):
    """
    Message handler is using for forwarding messages to appropriate controllers.
    Rules are configured in this class.
    """
    pass
