from abc import ABC, abstractmethod


class ILogger(ABC):
    """
    Class can be used for managing logging settings.
    Logs can be provided by controllers, views or framework classes
    """

    @abstractmethod
    def info(self, *args: str | bytes) -> None:
        """Save unimportant message"""
        raise NotImplementedError()

    @abstractmethod
    def warn(self, *args: str | bytes) -> None:
        """Save message that may be important"""
        raise NotImplementedError()

    @abstractmethod
    def error(self, *args: str | bytes) -> None:
        """Save error message that may be important"""
        raise NotImplementedError()

    @abstractmethod
    def critical(self, *args: str | bytes) -> None:
        """Process critical error (e.g. notifying administrator)"""
        raise NotImplementedError()


class ISysIOLogger(ILogger):
    """
    Logger that will log all messages to stdout or stderr
    """

    @abstractmethod
    def info(self, *args: str | bytes) -> None:
        """Save unimportant message to stdout"""
        raise NotImplementedError()

    @abstractmethod
    def warn(self, *args: str | bytes) -> None:
        """Save message that may be important to stdout"""
        raise NotImplementedError()

    @abstractmethod
    def error(self, *args: str | bytes) -> None:
        """Save error message that may be important to stdout"""
        raise NotImplementedError()

    @abstractmethod
    def critical(self, *args: str | bytes) -> None:
        """Save critical error to stdout"""
        raise NotImplementedError()
