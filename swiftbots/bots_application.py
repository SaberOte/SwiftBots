import asyncio
from typing import Callable, Optional

from swiftbots.runners import run_async
from swiftbots.loggers import SysIOLoggerFactory
from swiftbots.bots import Bot, _instantiate_in_bots
from swiftbots.types import IMessageHandler, IController, ILogger, IView, ILoggerFactory


class BotsApplication:

    __logger: ILogger = None
    __logger_factory: ILoggerFactory = None
    __bots: list[Bot] = []

    def __init__(self, logger_factory: ILoggerFactory = None):
        if logger_factory is None:
            logger_factory = SysIOLoggerFactory()
        self.use_logger(logger_factory)

    def use_logger(self, logger_factory: ILoggerFactory) -> None:
        """
        Set logger factory and create instance
        """
        assert isinstance(logger_factory, ILoggerFactory), 'Logger factory must be of type ILoggerFactory'
        self.__logger_factory = logger_factory
        self.__logger = logger_factory.get_logger()

    def add_bot(self, view_type: type[IView], controller_classes: list[type[IController]],
                message_handler_class: type[IMessageHandler] = None,
                name: Optional[str] = None, bot_logger_factory: ILoggerFactory = None) -> None:
        """
        Adds a bot with one view and some bound controllers. # TODO: add docstring
        """
        assert issubclass(view_type, IView), 'view must be of type IView'
        assert len(controller_classes) > 0, 'No controllers'
        assert (message_handler_class is None or issubclass(message_handler_class, IMessageHandler)), \
            'Message handler must be a TYPE and inherit IMessageHandler'
        for controller_type in controller_classes:
            assert issubclass(controller_type, IController), 'Controllers must be of type IController'
        assert (bot_logger_factory is None
                or isinstance(bot_logger_factory, ILoggerFactory)), 'Logger must be of type ILogger'

        bot_logger_factory = bot_logger_factory or self.__logger_factory
        self.__bots.append(Bot(view_type, controller_classes, message_handler_class, bot_logger_factory, name))

    def run(self, custom_runner: Callable = None) -> None:
        """
        Start application to listen all the bots in asynchronous event loop
        """
        if len(self.__bots) == 0:
            self.__logger.critical('No bots used')
            return

        _instantiate_in_bots(self.__bots)

        if custom_runner is None:
            asyncio.run(run_async(self.__bots))
        else:
            custom_runner(self.__bots)
