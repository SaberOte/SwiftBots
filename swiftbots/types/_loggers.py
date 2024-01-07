from abc import ABC, abstractmethod


class ILogger(ABC):
    """
    Class can be used for managing logging settings.
    Logs can be provided by controllers, views or framework classes
    """

    bot_name: str = None

    @abstractmethod
    async def info_async(self, *args, skip_prefix: bool = False) -> None:
        """Save an unimportant message"""
        raise NotImplementedError()

    @abstractmethod
    def info(self, *args, skip_prefix: bool = False) -> None:
        """Save an unimportant message"""
        raise NotImplementedError()

    @abstractmethod
    async def warn_async(self, *args, skip_prefix: bool = False) -> None:
        """Save a message that may be important"""
        raise NotImplementedError()

    @abstractmethod
    def warn(self, *args, skip_prefix: bool = False) -> None:
        """Save a message that may be important"""
        raise NotImplementedError()

    @abstractmethod
    async def error_async(self, *args, skip_prefix: bool = False) -> None:
        """Save an error message that may be important"""
        raise NotImplementedError()

    @abstractmethod
    def error(self, *args, skip_prefix: bool = False) -> None:
        """Save an error message that may be important"""
        raise NotImplementedError()

    @abstractmethod
    async def critical_async(self, *args, skip_prefix: bool = False) -> None:
        """Process a critical error (e.g. notifying administrator)"""
        raise NotImplementedError()

    @abstractmethod
    def critical(self, *args, skip_prefix: bool = False) -> None:
        """Process a critical error (e.g. notifying administrator)"""
        raise NotImplementedError()

    @abstractmethod
    async def report_async(self, *args, skip_prefix: bool = False) -> None:
        """Report to administrator some message"""
        raise NotImplementedError()

    @abstractmethod
    def report(self, *args, skip_prefix: bool = False) -> None:
        """Report to administrator"""
        raise NotImplementedError()


class ILoggerFactory:

    @abstractmethod
    def get_logger(self) -> ILogger:
        raise NotImplementedError()


class ILoggerProvider(ABC):

    @property
    def logger(self) -> 'ILogger':
        raise NotImplementedError()

    def _set_logger(self, logger: 'ILogger') -> None:
        raise NotImplementedError()
