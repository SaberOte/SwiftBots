import inspect
import logging
from collections.abc import Callable, Coroutine
from traceback import format_exc
from typing import Any

from swiftbots.all_types import ILogger, ILoggerFactory

report_func_type = Callable[[str], None]
report_async_func_type = Callable[[str], Coroutine[Any, Any, None]]


def logger_exc_catcher(func):
    """
    Using `logger_exc_catcher` is reasonable in methods where are used API
    requests to make a logger never throwable exceptions.
    """
    async def async_wrapper(*args, **kwargs) -> None:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logging.critical(f"[ERROR] Raised '{e.__class__.__name__}' when using logger:\n{e}.\n"
                             f"Full traceback: {format_exc()}")

    def sync_wrapper(*args, **kwargs) -> None:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.critical(f"[ERROR] Raised '{e.__class__.__name__}' when using logger:\n{e}.\n"
                             f"Full traceback: {format_exc()}")

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


class SysIOLogger(ILogger):

    def __init__(self, root_logger: logging.Logger) -> None:
        self._root_logger = root_logger

    async def debug_async(self, msg: str, *args, **kwargs) -> None:
        self._root_logger.debug(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs) -> None:
        self._root_logger.debug(msg, *args, **kwargs)

    async def info_async(self, msg: str, *args, **kwargs) -> None:
        self._root_logger.info(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        self._root_logger.info(msg, *args, **kwargs)

    async def warning_async(self, msg: str, *args, **kwargs) -> None:
        self._root_logger.warning(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self._root_logger.warning(msg, *args, **kwargs)

    async def error_async(self, msg: str, *args, **kwargs) -> None:
        self._root_logger.error(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self._root_logger.error(msg, *args, **kwargs)

    async def critical_async(self, msg: str, *args, **kwargs) -> None:
        self._root_logger.critical(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        self._root_logger.critical(msg, *args, **kwargs)

    async def exception_async(self, msg: str, *args, **kwargs) -> None:
        self._root_logger.exception(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs) -> None:
        self._root_logger.exception(msg, *args, **kwargs)

    async def report_async(self, msg: str) -> None:
        # SysIOLogger does not have an administrator channel for reporting by default
        self._root_logger.warning(msg)

    def report(self, msg: str) -> None:
        self._root_logger.warning(msg)


class AdminLogger(SysIOLogger):
    """
    A logger that logs the same as SysIOLogger, but it also reports
    to the administrator messages with levels ERROR, CRITICAL and EXCEPTION.
    Methods `report` and `report_async` send a message to an administrator
    directly and use level WARNING to log with base logging instance.
    """

    def __init__(self, report_func: report_func_type, async_report_func: report_async_func_type,
                 root_logger: logging.Logger):
        super().__init__(root_logger)
        self._report_func = report_func
        self._report_func_async = async_report_func

    async def error_async(self, msg: str, *args, **kwargs) -> None:
        await super().error_async(msg, *args, **kwargs)
        await self._call_report_func_async(msg)

    def error(self, msg: str, *args, **kwargs) -> None:
        super().error(msg, *args, **kwargs)
        self._call_report_func(msg)

    async def critical_async(self, msg: str, *args, **kwargs) -> None:
        await super().critical_async(msg, *args, **kwargs)
        await self._call_report_func_async(msg)

    def critical(self, msg: str, *args, **kwargs) -> None:
        super().error(msg, *args, **kwargs)
        self._call_report_func(msg)

    async def exception_async(self, msg: str, *args, **kwargs) -> None:
        await super().exception_async(msg, *args, **kwargs)
        await self._call_report_func_async(msg)

    def exception(self, msg: str, *args, **kwargs) -> None:
        super().exception(msg, *args, **kwargs)
        self._call_report_func(msg)

    async def report_async(self, msg: str) -> None:
        await super().warning_async(msg)
        await self._call_report_func_async(msg)

    def report(self, msg: str) -> None:
        super().warning(msg)
        self._call_report_func(msg)

    @logger_exc_catcher
    def _call_report_func(self, msg: str) -> None:
        self._report_func(msg)

    @logger_exc_catcher
    async def _call_report_func_async(self, msg: str) -> None:
        await self._report_func_async(msg)


class SysIOLoggerFactory(ILoggerFactory):

    def __init__(self, logger: logging.Logger | None = None):
        if logger is None:
            logging.basicConfig(level=logging.NOTSET)
            logger = logging.getLogger()
        self.logger = logger

    def get_logger(self) -> SysIOLogger:
        return SysIOLogger(self.logger)


class AdminLoggerFactory(SysIOLoggerFactory):

    def __init__(self, report_func: report_func_type, async_report_func: report_async_func_type,
                 logger: logging.Logger | None = None):
        super().__init__(logger)
        self.__report_func = report_func
        self.__report_func_async = async_report_func

    def get_logger(self) -> AdminLogger:
        return AdminLogger(self.__report_func, self.__report_func_async, self.logger)
