from abc import ABC, abstractmethod


class ILogger(ABC):
    """
    Class can be used for managing logging settings.
    Logs can be provided by controllers, views or framework classes
    """

    @abstractmethod
    def info(self, *args, **kwargs) -> None:
        """Save unimportant message"""
        raise NotImplementedError()

    @abstractmethod
    def warn(self, *args, **kwargs) -> None:
        """Save message that may be important"""
        raise NotImplementedError()

    @abstractmethod
    def error(self, *args, **kwargs) -> None:
        """Save error message that may be important"""
        raise NotImplementedError()

    @abstractmethod
    def critical(self, *args, **kwargs) -> None:
        """Process critical error (e.g. notifying administrator)"""
        raise NotImplementedError()


class ISysIOLogger(ILogger, ABC):
    """
    Logger that will log all messages to stdout or stderr
    """

    @abstractmethod
    def info(self, *args, **kwargs) -> None:
        """Save unimportant message to stdout"""
        raise NotImplementedError()

    @abstractmethod
    def warn(self, *args, **kwargs) -> None:
        """Save message that may be important to stdout"""
        raise NotImplementedError()

    @abstractmethod
    def error(self, *args, **kwargs) -> None:
        """Save error message that may be important to stdout"""
        raise NotImplementedError()

    @abstractmethod
    def critical(self, *args, **kwargs) -> None:
        """Save critical error to stdout"""
        raise NotImplementedError()
