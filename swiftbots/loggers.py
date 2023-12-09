from sys import stderr
from abc import ABC, abstractmethod


class LoggerInterface(ABC):
    """
    Class can be used for managing logging settings.
    Logs can be provided by controllers, views or framework classes
    """

    @abstractmethod
    def log(self, *args: str | bytes) -> None:
        """Log to somewhere"""
        raise NotImplementedError()

    @abstractmethod
    def error(self, *args: str | bytes) -> None:
        """Log error to somewhere"""
        raise NotImplementedError()

    @abstractmethod
    def critical(self, *args: str | bytes) -> None:
        """Process critical error (e.g. notifying administrator)"""
        raise NotImplementedError()


class StandardLogger(LoggerInterface):
    """
    Logger that will log all messages to stdout or stderr
    """

    def log(self, *args: str | bytes) -> None:
        """Log to stdout"""
        print(*args)

    def error(self, *args: str | bytes) -> None:
        """Log to stderr"""
        print(*args, file=stderr)

    def critical(self, *args: str | bytes) -> None:
        """Log to stderr"""
        self.error(*args)
