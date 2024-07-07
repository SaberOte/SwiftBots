__all__ = [
    'SwiftBots'
]

import asyncio
from collections.abc import Callable
from typing import Any, Dict, List, Optional, Type

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.ext.asyncio.session import async_sessionmaker

from swiftbots.all_types import IController, ILogger, ILoggerFactory, IMessageHandler, IScheduler, IView
from swiftbots.app.container import AppContainer
from swiftbots.bots import Bot, build_bots, build_scheduler
from swiftbots.loggers import SysIOLoggerFactory
from swiftbots.runners import run_async
from swiftbots.tasks.schedulers import SimpleScheduler
from swiftbots.tasks.tasks import TaskInfo


class SwiftBots:
    __bots: Dict[str, 'Bot']
    __logger: ILogger
    __logger_factory: ILoggerFactory
    __scheduler: IScheduler
    __runner: Callable[[AppContainer], Any]
    __db_engine: Optional[AsyncEngine] = None
    __db_session_maker: Optional[async_sessionmaker[AsyncSession]] = None

    def __init__(self,
                 logger_factory: Optional[ILoggerFactory] = None,
                 db_connection_string: Optional[str] = None,
                 scheduler: Optional[IScheduler] = None,
                 runner: Optional[Callable[[AppContainer], Any]] = None
                 ):
        assert logger_factory is None or isinstance(
            logger_factory, ILoggerFactory
        ), "Logger factory must be of type ILoggerFactory"

        self.__bots = {}
        # logger
        self.__logger_factory = logger_factory or SysIOLoggerFactory()
        self.__logger = self.__logger_factory.get_logger()

        # database
        if db_connection_string is not None:
            self.__db_engine = create_async_engine(db_connection_string, echo=False)
            self.__db_session_maker = async_sessionmaker(
                self.__db_engine, expire_on_commit=False
            )

        self.__scheduler = scheduler or SimpleScheduler()

        self.__runner = runner or run_async

    def add_bot(
        self,
        view: Type[IView],
        controllers: List[Type[IController]],
        tasks: Optional[List[TaskInfo]] = None,
        name: Optional[str] = None,
        message_handler: Optional[Type[IMessageHandler]] = None,
        bot_logger_factory: Optional[ILoggerFactory] = None,
    ) -> None:
        """
        The method adds a bot.
        It's required to have at least one controller and only one view in a bot.
        :param view: Class of a view.
        Must inherit BasicView, ChatView, TelegramView, VkontakteView or another.
        :param controllers: List of controllers. Required to have at least one controller.
        Must inherit Controller class.
        :param message_handler: Optional. Must inherit IMessageHandler.
        :param name: Optional. Set a name of the bot. ViewName if not provided. If no viewName, then random string.
        :param bot_logger_factory: Optional. Configure logger especially for this bot.
        """
        name = name or view.__name__
        assert name not in self.__bots, \
            f"Bot with the name {name} defined twice. If you want to use the same bots, give them different names"

        assert len(controllers) > 0, f"No controllers provided in {name} bot"

        assert issubclass(
            view, IView
        ), "The view must be of the type IView"

        assert message_handler is None or issubclass(
            message_handler, IMessageHandler
        ), "Message handler must be a TYPE and inherit IMessageHandler"

        for controller_type in controllers:
            assert issubclass(
                controller_type, IController
            ), "Controllers must be of type IController"

        assert bot_logger_factory is None or isinstance(
            bot_logger_factory, ILoggerFactory
        ), "Logger must be of type ILogger"

        bot_logger_factory = bot_logger_factory or self.__logger_factory
        tasks = tasks or []

        self.__bots[name] = Bot(
            controller_classes=controllers,
            view_class=view,
            task_infos=tasks,
            message_handler_class=message_handler,
            logger_factory=bot_logger_factory,
            name=name,
            db_session_maker=self.__db_session_maker,
        )

    def run(self) -> None:
        """
        Start application to listen to or execute all the bots
        """
        if len(self.__bots) == 0:
            self.__logger.critical("No bots used")
            return

        bots = list(self.__bots.values())

        build_bots(bots)
        build_scheduler(bots, self.__scheduler)
        app_container = AppContainer(bots, self.__logger, self.__scheduler)

        self.__runner(app_container)

        asyncio.run(self.__close_app())

    async def __close_app(self) -> None:
        if self.__db_engine is not None:
            await self.__db_engine.dispose()
