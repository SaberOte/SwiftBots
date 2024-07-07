__all__ = [
    'Bot',
    'build_bots',
    'soft_close_bot_async'
]

from collections.abc import Callable
from traceback import format_exc
from typing import Any, List, Optional, Type

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession

from swiftbots.all_types import (
    IController,
    ILogger,
    ILoggerFactory,
    IMessageHandler,
    IScheduler,
    IView,
)
from swiftbots.functions import call_raisable_function_async, decompose_bot_as_dependencies, resolve_function_args
from swiftbots.tasks.tasks import TaskInfo


class Bot:
    """A storage of controllers and views"""

    name: str
    __logger: ILogger
    __db_session_maker: Optional[async_sessionmaker[AsyncSession]] = None

    view_class: Type[IView]
    controller_classes: List[Type[IController]]
    message_handler_class: Optional[Type[IMessageHandler]]

    task_infos: List[TaskInfo]
    view: IView
    controllers: List[IController]
    message_handler: Optional[IMessageHandler]

    @property
    def logger(self) -> ILogger:
        return self.__logger

    @property
    def db_session_maker(self) -> Optional[async_sessionmaker[AsyncSession]]:
        return self.__db_session_maker

    def __init__(
        self,
        controller_classes: List[Type[IController]],
        view_class: Type[IView],
        task_infos: List[TaskInfo],
        message_handler_class: Optional[Type[IMessageHandler]],
        logger_factory: ILoggerFactory,
        name: str,
        db_session_maker: Optional[async_sessionmaker],
    ):
        self.view_class = view_class
        self.controller_classes = controller_classes
        self.task_infos = task_infos
        self.message_handler_class = message_handler_class
        self.name = name
        self.__logger = logger_factory.get_logger()
        self.__logger.bot_name = self.name
        self.__db_session_maker = db_session_maker


def build_views(bots: List[Bot]) -> None:
    """
    Instantiate and set views
    """
    for bot in bots:
        if bot.view_class:
            bot.view = bot.view_class()
            bot.view.init(bot, bot.logger, bot.db_session_maker)


def build_controllers(bots: List[Bot]) -> None:
    """
    Instantiate and set to the bot controllers, each one must be singleton
    """
    controller_memory: List[IController] = []
    for bot in bots:
        controllers_to_add: List[IController] = []
        controller_types = bot.controller_classes

        for controller_type in controller_types:
            found_instances = list(
                filter(lambda inst: controller_type is inst, controller_memory)
            )
            if len(found_instances) == 1:
                controller_instance = found_instances[0]
            elif len(found_instances) == 0:
                controller_instance = controller_type()
                controller_instance.init(bot.db_session_maker)
                controller_memory.append(controller_instance)
            else:
                raise Exception("Invalid algorithm")
            controllers_to_add.append(controller_instance)

        bot.controllers = controllers_to_add


def build_message_handlers(bots: List[Bot]) -> None:
    """
    Instantiate and set handlers
    """
    for bot in bots:
        if bot.view:
            if bot.message_handler_class is None:
                bot.message_handler_class = bot.view.default_message_handler_class
            bot.message_handler = bot.message_handler_class(bot.controllers, bot.logger)


def build_task_caller(info: TaskInfo, bot: Bot) -> Callable[..., Any]:
    func = info.func

    def caller() -> ...:
        min_deps = decompose_bot_as_dependencies(bot)
        args = resolve_function_args(func, min_deps)
        return func(**args)

    def wrapped_caller() -> any:
        return call_raisable_function_async(caller, bot)
    return wrapped_caller


def build_scheduler(bots: List[Bot], scheduler: IScheduler) -> None:
    task_names = set()
    for bot in bots:
        for task_info in bot.task_infos:
            assert task_info.name not in task_names, f'Task {task_info.name} met twice. Tasks must have different names'
            task_names.add(task_info.name)
            scheduler.add_task(task_info, build_task_caller(task_info, bot))
    task_names.clear()


def build_bots(bots: List[Bot]) -> None:
    """
    Instantiate and set to the bot instances, each controller must be singleton
    """
    build_views(bots)
    build_controllers(bots)
    build_message_handlers(bots)


async def soft_close_bot_async(bot: Bot) -> None:
    """
    Close bot's view softly to close all connections (like database or http clients)
    """
    # TODO: add this as a method to Bot and close all connections there
    try:
        await bot.view._soft_close_async()
    except Exception as e:
        await bot.logger.error_async(
            f"Raised an exception `{e}` when a bot closing method called:\n{format_exc()}"
        )
