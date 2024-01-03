from typing import Optional
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession

from swiftbots.types import IView, IController, IMessageHandler, ILogger, ILoggerFactory


class Bot:
    """A storage of controllers and views"""

    name: str
    __logger: ILogger = None
    __db_session_maker: Optional[async_sessionmaker[AsyncSession]] = None

    view_class: type[IView]
    controller_classes: list[type[IController]]
    message_handler_class: Optional[type[IMessageHandler]]

    view: IView
    controllers: list[IController]
    message_handler: IMessageHandler

    @property
    def logger(self) -> ILogger:
        return self.__logger

    @property
    def db_session_maker(self) -> async_sessionmaker[AsyncSession]:
        return self.__db_session_maker

    def __init__(self, view_class: type[IView], controller_classes: list[type[IController]],
                 message_handler_class: Optional[type[IMessageHandler]],
                 logger_factory: ILoggerFactory, name: str = None, db_session_maker: async_sessionmaker | None = None):
        self.view_class = view_class
        self.controller_classes = controller_classes
        self.message_handler_class = message_handler_class
        self.name = name or view_class.__name__
        self.__logger = logger_factory.get_logger()
        self.__logger.bot_name = self.name
        self.__db_session_maker = db_session_maker


def _set_views(bots: list[Bot]) -> None:
    """
    Instantiate and set views
    """
    for bot in bots:
        bot.view = bot.view_class()
        bot.view.init(bot)


def _set_controllers(bots: list[Bot]) -> None:
    """
    Instantiate and set to the bot controllers, each one must be singleton
    """
    controller_memory: list[IController] = []
    for bot in bots:
        controllers_to_add: list[IController] = []
        controller_types = bot.controller_classes

        for controller_type in controller_types:
            found_instances = list(filter(lambda inst: controller_type is inst, controller_memory))
            if len(found_instances) == 1:
                controller_instance = found_instances[0]
            elif len(found_instances) == 0:
                controller_instance = controller_type()
                controller_instance.init(bot.db_session_maker)
                controller_memory.append(controller_instance)
            else:
                raise Exception('Invalid algorithm')
            controllers_to_add.append(controller_instance)

        bot.controllers = controllers_to_add


def _set_message_handlers(bots: list[Bot]) -> None:
    """
    Instantiate and set handlers
    """
    for bot in bots:
        if bot.message_handler_class is None:
            bot.message_handler_class = bot.view_class.default_message_handler_class
        bot.message_handler = bot.message_handler_class(bot.controllers, bot.logger)


def _instantiate_in_bots(bots: list[Bot]) -> None:
    """
    Instantiate and set to the bot instances, each controller must be singleton
    """
    _set_views(bots)
    _set_controllers(bots)
    _set_message_handlers(bots)
