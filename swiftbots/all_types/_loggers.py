"""https://docs.python.org/3/library/logging.html"""
from abc import ABC, abstractmethod


class ILogger(ABC):
    """
    Class can be used for managing logging settings.
    Logs can be provided by controllers, views, tasks or framework classes
    """

    bot_name: str

    @abstractmethod
    async def debug_async(self, msg: str, *args, **kwargs) -> None:
        """Logs a message with level DEBUG on this logger"""
        raise NotImplementedError()

    @abstractmethod
    def debug(self, msg: str, *args, **kwargs) -> None:
        """Logs a message with level DEBUG on this logger"""
        raise NotImplementedError()

    @abstractmethod
    async def info_async(self, msg: str, *args, **kwargs) -> None:
        """Logs a message with level INFO on this logger"""
        raise NotImplementedError()

    @abstractmethod
    def info(self, msg: str, *args, **kwargs) -> None:
        """Logs a message with level INFO on this logger"""
        raise NotImplementedError()

    @abstractmethod
    async def warning_async(self, msg: str, *args, **kwargs) -> None:
        """Logs a message with level WARNING on this logger"""
        raise NotImplementedError()

    @abstractmethod
    def warning(self, msg: str, *args, **kwargs) -> None:
        """Logs a message with level WARNING on this logger"""
        raise NotImplementedError()

    @abstractmethod
    async def error_async(self, msg: str, *args, **kwargs) -> None:
        """Logs a message with level ERROR on this logger"""
        raise NotImplementedError()

    @abstractmethod
    def error(self, msg: str, *args, **kwargs) -> None:
        """Logs a message with level ERROR on this logger"""
        raise NotImplementedError()

    @abstractmethod
    async def critical_async(self, msg: str, *args, **kwargs) -> None:
        """Logs a message with level CRITICAL on this logger"""
        raise NotImplementedError()

    @abstractmethod
    def critical(self, msg: str, *args, **kwargs) -> None:
        """Logs a message with level CRITICAL on this logger"""
        raise NotImplementedError()

    @abstractmethod
    async def exception_async(self, msg: str, *args, **kwargs) -> None:
        """Logs a message with level ERROR on this logger.
        Exception info is added to the logging message.
        This method should only be called from an exception handler."""
        raise NotImplementedError()

    @abstractmethod
    def exception(self, msg: str, *args, **kwargs) -> None:
        """Logs a message with level ERROR on this logger.
        Exception info is added to the logging message.
        This method should only be called from an exception handler."""
        raise NotImplementedError()

    @abstractmethod
    async def report_async(self, msg: str) -> None:
        """
        If there's a configured report channel, send a message directly to an administrator.
        If there's no one, log a message with level WARNING.
        """
        raise NotImplementedError()

    @abstractmethod
    def report(self, msg: str) -> None:
        """
        If there's a configured report channel, send a message directly to an administrator.
        If there's no one, log a message with level WARNING.
        """
        raise NotImplementedError()


class ILoggerFactory:
    @abstractmethod
    def get_logger(self) -> ILogger:
        raise NotImplementedError()


class ILoggerProvider(ABC):
    @property
    def logger(self) -> "ILogger":
        raise NotImplementedError()

    def _set_logger(self, logger: "ILogger") -> None:
        raise NotImplementedError()
