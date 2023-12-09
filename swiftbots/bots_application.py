import asyncio
from typing import Type

from swiftbots.loggers import StandardLogger
from swiftbots.types import View, Controller, Bot, LoggerInterface


class BotsApplication:

    __logger: LoggerInterface
    __bots = []

    def add_bot(self, view_type: type[View], controller_types: list[type[Controller]]) -> None:
        """
        Adds a bot with one view and some bound controllers.
        """
        assert type(view_type) is Type, 'view_type must be class, not object'
        assert issubclass(view_type, View), 'View must be of type View'
        assert len(controller_types) > 0, 'No controllers'
        for controller_type in controller_types:
            assert type(controller_type) is Type, 'controller_types must be classes, not objects'
            assert issubclass(controller_type, Controller), 'Controllers must be of type Controller'

        self.__bots.append(Bot(view_type, controller_types))

    def run(self) -> None:
        if self.__logger is None:
            self.use_logger(StandardLogger())

        if len(self.__bots) == 0:
            self.__logger.error('No bots used')
            return
        if len(self.__bots) > 1:
            self.__logger.error('Cannot run more than one bots yet')
            return

        asyncio.run(instance.init_listen())

    def use_logger(self, logger: LoggerInterface) -> None:
        self.__logger = logger
