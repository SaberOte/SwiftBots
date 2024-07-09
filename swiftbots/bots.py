import asyncio
from collections.abc import Callable
from typing import Any, List, Optional, Union

from swiftbots.all_types import ILogger, ILoggerFactory, IScheduler, ITrigger
from swiftbots.functions import (
    call_raisable_function_async,
    decompose_bot_as_dependencies,
    generate_name,
    resolve_function_args,
)
from swiftbots.tasks.tasks import TaskInfo
from swiftbots.types import AsyncListenerFunction, DecoratedCallable


class Bot:
    """A storage of controllers and views"""

    @property
    def logger(self) -> ILogger:
        return self.__logger

    @property
    def is_enabled(self) -> bool:
        return self.__is_enabled

    def disable(self) -> None:
        self.__is_enabled = False

    def enable(self) -> None:
        self.__is_enabled = True

    def __init__(
        self,
        handler_func: DecoratedCallable,
        listener_func: AsyncListenerFunction,
        task_infos: List[TaskInfo],
        logger_factory: ILoggerFactory,
        name: str
    ):
        self.handler_func = handler_func
        self.listener_func = listener_func
        self.task_infos = task_infos
        self.name = name
        self.__logger = logger_factory.get_logger()
        self.__logger.bot_name = self.name
        self.__is_enabled = True


def build_task_caller(info: TaskInfo, bot: Bot) -> Callable[..., Any]:
    func = info.func

    def caller() -> Any:  # noqa: ANN401
        if bot.is_enabled:
            min_deps = decompose_bot_as_dependencies(bot)
            args = resolve_function_args(func, min_deps)
            return func(**args)

    def wrapped_caller() -> Any:  # noqa: ANN401
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


def disable_tasks(bot: Bot, scheduler: IScheduler) -> None:
    """Method is used to disable tasks when the bot is exiting or disabling."""
    scheduled_tasks = scheduler.list_tasks()
    bot_tasks = map(lambda ti: ti.name, bot.task_infos)
    for bot_task in bot_tasks:
        if bot_task in scheduled_tasks:
            scheduler.remove_task(bot_task)


async def stop_bot_async(bot: Bot, scheduler: IScheduler) -> None:
    bot.disable()
    disable_tasks(bot, scheduler)


class BasicBot:
    listener_func: AsyncListenerFunction
    handler_func: DecoratedCallable
    task_infos: List[TaskInfo]

    def __init__(
            self,
            name: Optional[str] = None,
            bot_logger_factory: Optional[ILoggerFactory] = None,
    ):
        assert bot_logger_factory is None or isinstance(
            bot_logger_factory, ILoggerFactory
        ), "Logger must be of type ILoggerFactory"

        self.name = name
        self.task_infos = list()
        self.bot_logger_factory = bot_logger_factory

    def listener(self) -> Callable[[DecoratedCallable], DecoratedCallable]:
        def wrapper(func: DecoratedCallable) -> DecoratedCallable:
            self.listener_func = func
            return func

        return wrapper

    def handler(self) -> Callable[[DecoratedCallable], DecoratedCallable]:
        def wrapper(func: DecoratedCallable) -> DecoratedCallable:
            self.handler_func = func
            return func

        return wrapper

    def task(
            self,
            triggers: Union[ITrigger, List[ITrigger]],
            run_at_start: bool = False,
            name: Optional[str] = None
    ) -> Callable[[DecoratedCallable], TaskInfo]:
        """
        Mark a bot method as a task.
        Will be executed by SwiftBots automatically.
        """
        assert isinstance(triggers, ITrigger) or isinstance(triggers, list), \
            'Trigger must be the type of ITrigger or a list of ITriggers'

        if isinstance(triggers, list):
            for trigger in triggers:
                assert isinstance(trigger, ITrigger), 'Triggers must be the type of ITrigger'
        assert isinstance(triggers, ITrigger) or len(triggers) > 0, 'Empty list of triggers'
        if name is None:
            name = generate_name()
        assert isinstance(name, str), 'Name must be a string'

        def wrapper(func: DecoratedCallable) -> TaskInfo:
            task_info = TaskInfo(name=name,
                                 func=func,
                                 triggers=triggers if isinstance(triggers, list) else [triggers],
                                 run_at_start=run_at_start)
            self.task_infos.append(task_info)
            return task_info

        return wrapper


class StubBot(BasicBot):
    """
    This class is used as a stub to allow a bot to run without a listener or a handler.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.listener_func = self.stub_listener
        self.handler_func = self.stub_handler

    async def stub_listener(self) -> AsyncListenerFunction:
        while True:
            await asyncio.sleep(1000000.)
            if False:
                yield {}

    async def stub_handler(self) -> None:
        await asyncio.sleep(0)
        return
