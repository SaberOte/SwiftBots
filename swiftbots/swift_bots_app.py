import asyncio
from collections.abc import Callable
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.ext.asyncio.session import async_sessionmaker

from swiftbots.tasks.schedulers import SimpleScheduler
from swiftbots.all_types import IController, ILogger, ILoggerFactory, IMessageHandler, IScheduler, IView
from swiftbots.bots import Bot, _instantiate_in_bots
from swiftbots.loggers import SysIOLoggerFactory
from swiftbots.runners import run_async


class SwiftBots:
    __logger: ILogger
    __logger_factory: ILoggerFactory
    __scheduler: IScheduler
    __db_engine: Optional[AsyncEngine] = None
    __db_session_maker: Optional[async_sessionmaker[AsyncSession]] = None
    __bots: list[Bot]

    def __init__(self,
                 logger_factory: Optional[ILoggerFactory] = None,
                 db_connection_string: Optional[str] = None,
                 scheduler: Optional[IScheduler] = None
                 ):
        assert isinstance(
            logger_factory, ILoggerFactory
        ), "Logger factory must be of type ILoggerFactory"

        self.__bots = []
        # logger
        self.__logger_factory = logger_factory or SysIOLoggerFactory()
        self.__logger = logger_factory.get_logger()

        # database
        if db_connection_string is not None:
            self.__db_engine = create_async_engine(db_connection_string, echo=False)
            self.__db_session_maker = async_sessionmaker(
                self.__db_engine, expire_on_commit=False
            )

        self.__scheduler = scheduler or SimpleScheduler()

    def add_bot(
        self,
        view_class: type[IView],
        controller_classes: list[type[IController]],
        name: str | None = None,
        message_handler_class: type[IMessageHandler] | None = None,
        bot_logger_factory: ILoggerFactory | None = None,
    ) -> None:
        """
        The method adds a bot.
        It's required to have at least one controller and only one view in a bot.
        :param view_class: Class of a view.
        Must inherit BasicView, ChatView, TelegramView, VkontakteView or another.
        :param controller_classes: List of controllers. Required to have at least one controller.
        Must inherit Controller class.
        :param message_handler_class: Optional. Must inherit IMessageHandler.
        :param name: Optional. Set a name of the bot. ViewName if not provided. If no viewName, then random string.
        :param bot_logger_factory: Optional. ILoggerFactory to configure logger.
        """
        assert len(controller_classes) > 0, "No controllers"

        assert issubclass(
            view_class, IView
        ), "view must be of type IView"

        assert message_handler_class is None or issubclass(
            message_handler_class, IMessageHandler
        ), "Message handler must be a TYPE and inherit IMessageHandler"

        for controller_type in controller_classes:
            assert issubclass(
                controller_type, IController
            ), "Controllers must be of type IController"

        assert bot_logger_factory is None or isinstance(
            bot_logger_factory, ILoggerFactory
        ), "Logger must be of type ILogger"

        name = name or view_class.__name__
        bot_logger_factory = bot_logger_factory or self.__logger_factory

        self.__bots.append(
            Bot(
                controller_classes,
                view_class,
                message_handler_class,
                bot_logger_factory,
                name,
                self.__db_session_maker,
            )
        )

    def run(self, custom_runner: Callable[[list["Bot"]], None] | None = None) -> None:
        """
        Start application to listen to all the bots in asynchronous event loop
        """
        if len(self.__bots) == 0:
            self.__logger.critical("No bots used")
            return

        self.__check_bot_repeats()

        _instantiate_in_bots(self.__bots)

        if custom_runner is None:
            asyncio.run(run_async(self.__bots))
        else:
            custom_runner(self.__bots)

        asyncio.run(self.__close_app())

    async def __close_app(self) -> None:
        if self.__db_engine is not None:
            await self.__db_engine.dispose()

    def __check_bot_repeats(self) -> None:
        names = set()
        for bot in self.__bots:
            assert (
                bot.name not in names
            ), f"Bot {bot.name} is defined twice. If you want to use same bots, give them different names"
            names.add(bot.name)
