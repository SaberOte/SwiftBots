import asyncio
from typing import ClassVar, Callable
from enum import Enum

from swiftbots.loggers import SysIOLogger
from swiftbots.types import IMessageHandler, IController, ILogger, IView
from swiftbots.bots import Bot, _instantiate_in_bots
from swiftbots.message_handlers import MultiControllerMessageHandler
from swiftbots.runners import run_async


DEFAULT_MESSAGE_HANDLER_TYPE = MultiControllerMessageHandler


class RunnerMode(Enum):
    ASYNCHRONOUSLY = 1
    SYNCHRONOUSLY = 2
    MULTITHREADING = 3
    CUSTOM = 4


class BotsApplication:

    __logger: ILogger = None
    __bots: list[Bot] = []

    def __init__(self, logger: ILogger = None):
        if logger is None:
            self.use_logger(SysIOLogger())
        self.use_logger(logger)

    def use_logger(self, logger: ILogger) -> None:
        """
        Set logger instance
        """
        assert isinstance(logger, ILogger), 'Logger must be of type ILogger'
        self.__logger = logger

    def add_bot(self, view_type: type[IView], controller_types: list[type[IController]],
                message_handler_type: type[IMessageHandler] = None) -> None:
        """
        Adds a bot with one view and some bound controllers.
        """
        assert issubclass(view_type, IView), 'view must be of type IView'
        assert len(controller_types) > 0, 'No controllers'
        assert (message_handler_type is None or issubclass(message_handler_type, IMessageHandler))
        for controller_type in controller_types:
            assert issubclass(controller_type, IController), 'Controllers must be of type IController'

        if message_handler_type is None:
            message_handler_type = DEFAULT_MESSAGE_HANDLER_TYPE
        self.__bots.append(Bot(view_type, controller_types, message_handler_type, self.__logger))

    def run(self, mode: RunnerMode = RunnerMode.ASYNCHRONOUSLY, custom_runner: Callable = None) -> None:
        """
        Start application to listen all the bots in asynchronous event loop
        """
        assert isinstance(mode, RunnerMode)
        assert mode != RunnerMode.CUSTOM or custom_runner is not None, \
            'Custom runner must be provided as argument if chosen custom run mode'

        if len(self.__bots) == 0:
            self.__logger.critical('No bots used')
            return

        _instantiate_in_bots(self.__bots)

        if mode == RunnerMode.ASYNCHRONOUSLY:
            asyncio.run(run_async(self.__bots))
        elif mode == RunnerMode.SYNCHRONOUSLY:
            # TODO: make synchronous mode
            self.__logger.critical('Can be run only asynchronous mode yet')
        elif mode == RunnerMode.MULTITHREADING:
            # TODO: make multithread mode
            self.__logger.critical('Can be run only asynchronous mode yet')
        elif mode == RunnerMode.CUSTOM:
            custom_runner(self.__bots)
        else:
            self.__logger.critical(f'Invalid mode was chosen to run {type(self).__name__}')
