from collections.abc import Callable
from typing import Any, Dict, List, Optional, Union

from swiftbots.all_types import ILogger, ILoggerFactory, IScheduler
from swiftbots.app.container import AppContainer
from swiftbots.bots import BasicBot, Bot, build_scheduler
from swiftbots.functions import generate_name
from swiftbots.loggers import SysIOLoggerFactory
from swiftbots.runners import run_async
from swiftbots.tasks.schedulers import SimpleScheduler


class SwiftBots:
    def __init__(self,
                 logger_factory: Optional[ILoggerFactory] = None,
                 scheduler: Optional[IScheduler] = None,
                 runner: Optional[Callable[[AppContainer], Any]] = None
                 ):
        assert logger_factory is None or isinstance(
            logger_factory, ILoggerFactory
        ), "Logger factory must be of type ILoggerFactory"

        self.__bots: Dict[str, Bot] = {}
        self.__logger_factory: ILoggerFactory = logger_factory or SysIOLoggerFactory()
        self.__logger: ILogger = self.__logger_factory.get_logger()
        self.__scheduler: IScheduler = scheduler or SimpleScheduler()
        self.__runner: Callable[[AppContainer], Any] = runner or run_async

    def add_bot(self, bot: BasicBot) -> None:
        assert isinstance(bot, BasicBot), "Bot must be of type BasicBot or an inherited class"

        name = bot.name or generate_name()
        assert name not in self.__bots, \
            f"Bot with the name {name} defined twice. If you want to use the same bots, you give them different names"

        members = vars(bot)
        assert 'listener_func' in members, 'You have to set a listener or use different type of a bot'
        assert 'handler_func' in members, 'You have to set a handler or use different type of a bot'

        bot_logger_factory = bot.bot_logger_factory or self.__logger_factory

        self.__bots[name] = Bot(
            handler_func=bot.handler_func,
            listener_func=bot.listener_func,
            task_infos=bot.task_infos,
            logger_factory=bot_logger_factory,
            name=name,
        )

    def add_bots(self, bots: Union[BasicBot, List[BasicBot]]) -> None:
        if isinstance(bots, list):
            for bot in bots:
                self.add_bot(bot)
        elif isinstance(bots, BasicBot):
            self.add_bot(bots)
        else:
            raise AssertionError('bots must be a type of a list of BasicBot or an inherited class')

    def run(self) -> None:
        """
        Start application to listen to or execute all the bots
        """
        if len(self.__bots) == 0:
            self.__logger.critical("No bots used")
            return

        bots = list(self.__bots.values())

        build_scheduler(bots, self.__scheduler)
        app_container = AppContainer(bots, self.__logger, self.__scheduler)

        self.__runner(app_container)
