import asyncio
import random
import string

from typing import Callable, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.ext.asyncio.session import async_sessionmaker

from swiftbots.runners import run_async
from swiftbots.loggers import SysIOLoggerFactory
from swiftbots.bots import Bot, _instantiate_in_bots
from swiftbots.types import IMessageHandler, IController, ILogger, IView, ILoggerFactory, ITask


class BotsApplication:

    __logger: ILogger = None
    __logger_factory: ILoggerFactory = None
    __db_engine: Optional[AsyncEngine] = None
    __db_session_maker: Optional[async_sessionmaker[AsyncSession]] = None
    __bots: list[Bot] = None

    def __init__(self, logger_factory: ILoggerFactory = None):
        self.__bots = []
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

    def use_database(self, connection_string: str, pool_size: int = 5, max_overflow: int = 10) -> None:
        """
        This method must be called before adding bots to an app!
        Examples of connections string:
        sqlite+aiosqlite://~/tmp/db.sqlite3,
        postgresql+asyncpg://nick:password123@localhost/database123,
        mysql+asyncmy://nick:password123@localhost/database123.
        It's necessary to use async drivers for database connection.
        """
        self.__db_engine = create_async_engine(connection_string, echo=False)
        self.__db_session_maker = async_sessionmaker(self.__db_engine, expire_on_commit=False)

    def add_bot(self, view_class: type[IView] | None, controller_classes: list[type[IController]],
                task_classes: list[type[ITask]] = None, message_handler_class: type[IMessageHandler] = None,
                name: Optional[str] = None, bot_logger_factory: ILoggerFactory = None) -> None:
        """
        Adds a bot. It's required to have at least one controller in a bot.
        And there's required to contain either one view or at least one task (or both).
        :param view_class: class of view. Must inherit BasicView, ChatView, TelegramView, VkontakteView or another.
        :param controller_classes: list of controllers. Required to have at least one controller.
        Must inherit Controller class.
        :param task_classes: task classes. Tasks inherit ITask. Do scheduled tasks.
        :param message_handler_class: Optional. Must inherit IMessageHandler.
        :param name: Optional. Set a name of the bot. ViewName if not provided. If no viewName, then random string.
        :param bot_logger_factory: Optional. ILoggerFactory to configure logger.
        """
        assert len(controller_classes) > 0, 'No controllers'
        assert view_class is None or issubclass(view_class, IView), 'view must be of type IView'
        assert task_classes is None or len(task_classes) > 0, 'Empty task classes list provided'
        assert task_classes or view_class, 'Required to have at least either tasks or view'
        assert (message_handler_class is None or issubclass(message_handler_class, IMessageHandler)), \
            'Message handler must be a TYPE and inherit IMessageHandler'
        for controller_type in controller_classes:
            assert issubclass(controller_type, IController), 'Controllers must be of type IController'
        if task_classes:
            for task_class in task_classes:
                assert issubclass(task_class, ITask), 'Tasks must be of type ITask'
        assert (bot_logger_factory is None
                or isinstance(bot_logger_factory, ILoggerFactory)), 'Logger must be of type ILogger'

        if not name:
            if view_class:
                name = view_class.__name__
            else:
                name = ''.join(random.choices(string.ascii_letters, k=8))

        bot_logger_factory = bot_logger_factory or self.__logger_factory
        self.__bots.append(Bot(controller_classes, view_class, task_classes, message_handler_class,
                               bot_logger_factory, name, self.__db_session_maker))

    def run(self, custom_runner: Callable = None) -> None:
        """
        Start application to listen all the bots in asynchronous event loop
        """
        if len(self.__bots) == 0:
            self.__logger.critical('No bots used')
            return

        self.__check_bot_repeats()

        _instantiate_in_bots(self.__bots)

        if custom_runner is None:
            asyncio.run(run_async(self.__bots))
        else:
            custom_runner(self.__bots)

        asyncio.run(self.__close_app())

    async def __close_app(self):
        if self.__db_engine is not None:
            await self.__db_engine.dispose()

    def __check_bot_repeats(self) -> None:
        names = set()
        for bot in self.__bots:
            assert bot.name not in names, \
                f'Bot {bot.name} is defined twice. If you want to use same bots, give them different names'
            names.add(bot.name)
