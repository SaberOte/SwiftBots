from abc import ABC, abstractmethod
from typing import Callable, Optional, TYPE_CHECKING, Awaitable

if TYPE_CHECKING:
    from swiftbots.types import ILogger, IView, Bot


class IController(ABC):

    _logger: 'ILogger' = None
    _bot: 'Bot' = None
    cmds: dict[str, Callable] = {}
    default: Optional[Callable[['IView', dict], Awaitable]] = None

    @abstractmethod
    def init(self, logger: 'ILogger', bot: 'Bot') -> None:
        """Set all necessary attributes"""
        raise NotImplementedError()

    @abstractmethod
    def info(self, *args, **kwargs) -> None:
        """If standard logger wasn't replaced, logs to stdout"""
        raise NotImplementedError()

    @abstractmethod
    def warn(self, *args, **kwargs) -> None:
        """If standard logger wasn't replaced, logs to stdout"""
        raise NotImplementedError()

    @abstractmethod
    def error(self, *args, **kwargs) -> None:
        """If standard logger wasn't replaced, logs to stderr"""
        raise NotImplementedError()

    @abstractmethod
    def critical(self, *args, **kwargs) -> None:
        """If standard logger wasn't replaced, logs to stderr"""
        raise NotImplementedError()
