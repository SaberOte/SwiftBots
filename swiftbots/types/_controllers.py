from abc import ABC, abstractmethod
from typing import Callable, Optional, TYPE_CHECKING, Awaitable

if TYPE_CHECKING:
    from swiftbots.types import ILogger, IView


class IController(ABC):

    __logger: 'ILogger' = None
    cmds: dict[str, Callable] = {}
    default: Optional[Callable[['IView', dict], Awaitable]] = None

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

    @abstractmethod
    def _set_logger(self, logger: 'ILogger') -> None:
        """Set needed logger for this controller"""
        raise NotImplementedError()
