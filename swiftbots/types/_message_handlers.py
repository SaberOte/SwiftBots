"""
Message handler is using for executing commands in appropriate controller.
Rules configuring in message handler classes.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiftbots.types import IView, IController, ILogger


class MessageHandlingResult(Enum):
    SUCCESS = 1
    ERROR = 2
    DEFAULT_HANDLER_INVOKED = 3
    NO_MATCHES = 4


class IMessageHandler(ABC):
    """
    Abstract class of Message Handler
    """

    @abstractmethod
    def __init__(self, controllers: list['IController'], logger: 'ILogger'):
        raise NotImplementedError()

    @abstractmethod
    async def handle_message_async(self, view: 'IView', context: dict):
        """Accept message and execute it in appropriate controller"""
        raise NotImplementedError()


class IBasicMessageHandler(IMessageHandler, ABC):
    """
    Defines exactly one controller. Untouched message just
    will be processed in `default` method of it.
    """
    pass


class IMultiControllerMessageHandler(IMessageHandler, ABC):
    """
    Message handler is using for forwarding messages to appropriate controllers.
    Rules are configured in this class.
    """
    pass
