from typing import TYPE_CHECKING
from abc import ABC

from swiftbots.types import IController

if TYPE_CHECKING:
    from swiftbots.bots import Bot
    from swiftbots.types import ILogger


class Controller(IController, ABC):

    def init(self, logger: 'ILogger', bot: 'Bot') -> None:
        self._logger = logger
        self._bot = bot

    def info(self, *args: str | bytes) -> None:
        self._logger.info(*args)

    def warn(self, *args: str | bytes) -> None:
        self._logger.warn(*args)

    def error(self, *args: str | bytes) -> None:
        self._logger.error(*args)

    def critical(self, *args: str | bytes) -> None:
        self._logger.critical(*args)
