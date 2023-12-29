import inspect

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
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            print_stderr('[ERROR]', f"Raised {e.__class__.__name__} when using logger: {e}.\n"
                                    f"Full traceback: {format_exc()}")

    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print_stderr('[ERROR]', f"Raised {e.__class__.__name__} when using logger: {e}.\n"
                                    f"Full traceback: {format_exc()}")

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


class SysIOLogger(ILogger):

    def __init__(self, skip_prefix: bool) -> None:
        self.__skip_prefix = skip_prefix

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

    def _build_prefix(self, message_type: str, skip_prefix: bool = None, skip_message_type: bool = False) -> str:
        if skip_prefix or skip_prefix is None and self.__skip_prefix:
            return ''
        if skip_message_type and self.bot_name:
            return f'[{self.bot_name}] '
        if self.bot_name:
            return f'[{message_type} {self.bot_name}] '
        return f'[{message_type}] '


class AdminLogger(SysIOLogger):

    def __init__(self, report_func: Callable, async_report_func: Callable, skip_prefix: bool):
        super().__init__(skip_prefix)
        self.__report_func = report_func
        self.__report_func_async = async_report_func

    @exc_wrapper
    async def report_async(self, *args, **kwargs) -> None:
        """
        Log a message and report to administrator.
        Method with messaging to administrator must be
        provided in constructor of this logger
        """
        await self.__stderr_and_report('REPORT', *args, is_async=True, is_stderr=False, **kwargs)

    @exc_wrapper
    def report(self, *args, **kwargs) -> None:
        """
        Log a message and report to administrator.
        Method with messaging to administrator must be
        provided in constructor of this logger
        """
        self.__stderr_and_report('REPORT', *args, is_async=False, is_stderr=False, **kwargs)

    @exc_wrapper
    async def error_async(self, *args, **kwargs) -> None:
        """
        Log a message and report to administrator.
        Method with messaging to administrator must be
        provided in constructor of this logger
        """
        await self.__stderr_and_report('ERROR', *args, is_async=True, is_stderr=True, **kwargs)
        
    @exc_wrapper
    def error(self, *args, **kwargs) -> None:
        """
        Log a message and report to administrator.
        Method with messaging to administrator must be
        provided in constructor of this logger
        """
        self.__stderr_and_report('ERROR', *args, is_async=False, is_stderr=True, **kwargs)
        
    @exc_wrapper
    async def critical_async(self, *args, **kwargs) -> None:
        """
        Log a message and report to administrator.
        Method with messaging to administrator must be
        provided in constructor of this logger
        """
        await self.__stderr_and_report('CRITICAL', *args, is_async=True, is_stderr=True, **kwargs)
    
    @exc_wrapper
    def critical(self, *args, **kwargs) -> None:
        """
        Log a message and report to administrator.
        Method with messaging to administrator must be
        provided in constructor of this logger
        """
        self.__stderr_and_report('CRITICAL', *args, is_async=False, is_stderr=True, **kwargs)

    def __stderr_and_report(self, reason: str, *args, is_async: bool, is_stderr: bool, **kwargs):
        prefix = self._build_prefix(reason, **kwargs)
        message = ' '.join([str(arg) for arg in args])
        if is_stderr:
            print_stderr(prefix+message)
        else:
            print_stdout(prefix+message)
        if is_async:
            return self.__report_func_async(message)
        return self.__report_func(message)


class SysIOLoggerFactory(ILoggerFactory):

    def __init__(self, skip_prefix: bool = False):
        self.skip_prefix = skip_prefix

    def get_logger(self) -> SysIOLogger:
        return SysIOLogger(self.skip_prefix)


class AdminLoggerFactory(ILoggerFactory):

    def __init__(self, report_func: Callable, async_report_func: Callable, skip_prefix: bool = False):
        self.__report_func = report_func
        self.__report_func_async = async_report_func
        self.__skip_prefix = skip_prefix

    def get_logger(self) -> AdminLogger:
        return AdminLogger(self.__report_func, self.__report_func_async, self.__skip_prefix)
