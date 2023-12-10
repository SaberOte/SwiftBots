from abc import ABC, abstractmethod
from asyncio import coroutine
from typing import Callable, Optional

from swiftbots.types import ILogger, IView


class IController(ABC):

    __logger: ILogger = None
    cmds: dict[str, Callable] = {}
    default: Optional[Callable[[IView, dict], coroutine]] = None

    @abstractmethod
    def info(self, *args: str | bytes) -> None:
        """If standard logger wasn't replaced, logs to stdout"""
        raise NotImplementedError()

    @abstractmethod
    def warn(self, *args: str | bytes) -> None:
        """If standard logger wasn't replaced, logs to stdout"""
        raise NotImplementedError()

    @abstractmethod
    def error(self, *args: str | bytes) -> None:
        """If standard logger wasn't replaced, logs to stderr"""
        raise NotImplementedError()

    @abstractmethod
    def critical(self, *args: str | bytes) -> None:
        """If standard logger wasn't replaced, logs to stderr"""
        raise NotImplementedError()

    @abstractmethod
    def _set_logger(self, logger: ILogger) -> None:
        """Set needed logger for this controller"""
        raise NotImplementedError()
