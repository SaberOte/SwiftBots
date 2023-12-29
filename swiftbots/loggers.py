from sys import stderr, stdout
from typing import Callable
from traceback import format_exc

from swiftbots.types import ILogger, ILoggerFactory


def print_stdout(*args, **kwargs) -> None:
    print(*args, file=stdout, **kwargs)


def print_stderr(*args, **kwargs) -> None:
    print(*args, file=stderr, **kwargs)


def exc_wrapper(func):
    """
    Using exc_wrapper is reasonable in methods where are used API
    requests in order to make a logger never throwable exceptions
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            print_stderr('[ERROR]', f"Raised {e.__class__.__name__} when using logger: {e}.\n"
                                    f"Full traceback: {format_exc()}")
    return wrapper


class SysIOLogger(ILogger):

    def info(self, *args, **kwargs) -> None:
        """Save a message to stdout"""
        prefix = self._build_prefix('INFO', **kwargs)
        print_stdout(prefix, *args, **kwargs)

    def warn(self, *args, **kwargs) -> None:
        """Save a message to stderr"""
        prefix = self._build_prefix('WARN', **kwargs)
        print_stderr(prefix, *args, **kwargs)

    def error(self, *args, **kwargs) -> None:
        """Save an error message to stderr"""
        prefix = self._build_prefix('ERROR', **kwargs)
        print_stderr(prefix, *args, **kwargs)

    def critical(self, *args, **kwargs) -> None:
        """Save a critical message to stderr"""
        prefix = self._build_prefix('CRITICAL', **kwargs)
        print_stderr(prefix, *args, **kwargs)

    def report(self, *args, **kwargs) -> None:
        """Save a report message to stderr"""
        prefix = self._build_prefix('REPORT', **kwargs)
        print_stderr(prefix, *args, **kwargs)

    async def info_async(self, *args, **kwargs) -> None:
        """Save a message to stdout"""
        self.info(*args, **kwargs)

    async def warn_async(self, *args, **kwargs) -> None:
        """Save a message to stderr"""
        self.warn(*args, **kwargs)

    async def error_async(self, *args, **kwargs) -> None:
        """Save an error message to stderr"""
        self.error(*args, **kwargs)

    async def critical_async(self, *args, **kwargs) -> None:
        """Save a critical message to stderr"""
        self.critical(*args, **kwargs)

    async def report_async(self, *args, **kwargs) -> None:
        """Save a report message to stderr"""
        self.report(*args, **kwargs)

    def _build_prefix(self, message_type: str, skip_prefix: bool = False) -> str:
        if skip_prefix:
            return ''
        if self.bot_name:
            return f'[{message_type} {self.bot_name}] '
        return f'[{message_type}] '


class AdminLogger(SysIOLogger):

    __report_func: Callable
    __report_func_async: Callable

    def __init__(self, report_func: Callable, async_report_func: Callable):
        self.__report_func = report_func
        self.__report_func_async = async_report_func

    @exc_wrapper
    async def report_async(self, *args, **kwargs) -> None:
        """
        Log a message and report to administrator.
        Method with messaging to administrator must be
        provided in constructor of this logger
        """
        prefix = self._build_prefix('REPORT', **kwargs)
        print_stdout(prefix, *args, **kwargs)
        message = prefix + ' '.join([str(arg) for arg in args])
        await self.__report_func_async(message)

    @exc_wrapper
    def report(self, *args, **kwargs) -> None:
        """
        Log a message and report to administrator.
        Method with messaging to administrator must be
        provided in constructor of this logger
        """
        prefix = self._build_prefix('REPORT', **kwargs)
        print_stdout(prefix, *args, **kwargs)
        message = prefix + ' '.join([str(arg) for arg in args])
        self.__report_func(message)

    @exc_wrapper
    async def error_async(self, *args, **kwargs) -> None:
        """
        Log a message and report to administrator.
        Method with messaging to administrator must be
        provided in constructor of this logger
        """
        prefix = self._build_prefix('ERROR', **kwargs)
        print_stderr(prefix, *args, **kwargs)
        message = prefix + ' '.join([str(arg) for arg in args])
        await self.__report_func_async(message)
        
    @exc_wrapper
    def error(self, *args, **kwargs) -> None:
        """
        Log a message and report to administrator.
        Method with messaging to administrator must be
        provided in constructor of this logger
        """
        prefix = self._build_prefix('ERROR', **kwargs)
        print_stderr(prefix, *args, **kwargs)
        message = prefix + ' '.join([str(arg) for arg in args])
        self.__report_func(message)
        
    @exc_wrapper
    async def critical_async(self, *args, **kwargs) -> None:
        """
        Log a message and report to administrator.
        Method with messaging to administrator must be
        provided in constructor of this logger
        """
        prefix = self._build_prefix('CRITICAL', **kwargs)
        print_stderr(prefix, *args, **kwargs)
        message = prefix + ' '.join([str(arg) for arg in args])
        await self.__report_func_async(message)
    
    @exc_wrapper
    def critical(self, *args, **kwargs) -> None:
        """
        Log a message and report to administrator.
        Method with messaging to administrator must be
        provided in constructor of this logger
        """
        prefix = self._build_prefix('CRITICAL', **kwargs)
        print_stderr(prefix, *args, **kwargs)
        message = prefix + ' '.join([str(arg) for arg in args])
        self.__report_func(message)


class SysIOLoggerFactory(ILoggerFactory):

    def get_logger(self) -> SysIOLogger:
        return SysIOLogger()


class AdminLoggerFactory(ILoggerFactory):

    __report_func: Callable
    __report_func_async: Callable

    def __init__(self, report_func: Callable, async_report_func: Callable):
        self.__report_func = report_func
        self.__report_func_async = async_report_func

    def get_logger(self) -> AdminLogger:
        return AdminLogger(self.__report_func, self.__report_func_async)
