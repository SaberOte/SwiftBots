from swiftbots.types import ILogger, IController


class Controller(IController):

    def info(self, *args: str | bytes) -> None:
        self.__logger.info(*args)

    def warn(self, *args: str | bytes) -> None:
        self.__logger.warn(*args)

    def error(self, *args: str | bytes) -> None:
        self.__logger.error(*args)

    def critical(self, *args: str | bytes) -> None:
        self.__logger.critical(*args)

    def _set_logger(self, logger: ILogger) -> None:
        self.__logger = logger
