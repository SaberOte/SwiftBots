from abc import ABC

from swiftbots.types import LoggerInterface


class Controller(ABC):

    __logger: LoggerInterface

    def log(self, *args: str | bytes) -> None:
        """If standard logger wasn't replaced, logs to stdout"""
        self.__logger.log(*args)

    def error(self, *args: str | bytes) -> None:
        """If standard logger wasn't replaced, logs to stderr"""
        self.__logger.error(*args)

    def critical(self, *args: str | bytes) -> None:
        """If standard logger wasn't replaced, logs to stderr"""
        self.__logger.critical(*args)

    def _set_logger(self, logger: LoggerInterface) -> None:
        self.__logger = logger
