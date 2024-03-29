from abc import ABC
from typing import TYPE_CHECKING

from swiftbots.all_types import ILoggerProvider

if TYPE_CHECKING:
    from swiftbots.all_types import ILogger


class AbstractLoggerProvider(ILoggerProvider, ABC):
    __logger: "ILogger"

    @property
    def logger(self) -> "ILogger":
        return self.__logger

    def _set_logger(self, logger: "ILogger") -> None:
        self.__logger = logger
