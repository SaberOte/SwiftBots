import asyncio
from collections.abc import Callable
from typing import Any, Coroutine, List, Optional, TypeVar, Union

from swiftbots.all_types import ILogger, ILoggerFactory, IScheduler, ITrigger
from swiftbots.chats import Chat
from swiftbots.functions import (
    call_raisable_function_async,
    decompose_bot_as_dependencies,
    generate_name,
    resolve_function_args,
)
from swiftbots.loggers import SysIOLoggerFactory
from swiftbots.message_handlers import (
    ChatMessageHandler1,
    CompiledChatCommand,
    compile_chat_commands,
    handle_message,
)
from swiftbots.tasks.tasks import TaskInfo
from swiftbots.types import AsyncListenerFunction, AsyncSenderFunction, DecoratedCallable


class Bot:
    """Base class for all other types of bots.
    This bot can only have a listener, a handler or tasks"""
    listener_func: AsyncListenerFunction
    handler_func: DecoratedCallable
    task_infos: List[TaskInfo]
    __logger: ILogger

    def __init__(
        self,
        name: Optional[str] = None,
        bot_logger_factory: Optional[ILoggerFactory] = None,
    ):
        assert bot_logger_factory is None or isinstance(
            bot_logger_factory, ILoggerFactory
        ), "Logger must be of type ILoggerFactory"

        self.task_infos = list()
        self.name: str = name or generate_name()
        bot_logger_factory = bot_logger_factory or SysIOLoggerFactory()
        self.__logger = bot_logger_factory.get_logger()
        self.__logger.bot_name = self.name
        self.__is_enabled = True

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

    def before_start(self) -> None:
        """
        Do something right before the app starts.
        Need to override this method.
        Use it like `super().before_start_async()`.
        """
        # TODO: do assert, check if listener_func is exist in self
        ...


class StubBot(Bot):
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


class ChatBot(Bot):
    Chat = TypeVar('Chat', bound=Chat)
    _sender_func: AsyncSenderFunction
    _compiled_chat_commands: List[CompiledChatCommand]
    _default_handler_func: Optional[DecoratedCallable] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._message_handlers: List[ChatMessageHandler1] = list()

        def handler(message: str, sender: Union[str, int], all_deps: dict[str, Any]) -> Coroutine:
            chat = Chat(sender, message, self._sender_func, self.logger)
            all_deps['chat'] = chat
            return self.overridden_handler(message, chat, all_deps)
        self.handler_func = handler

    def message_handler(self, commands: List[str]) -> DecoratedCallable:
        assert isinstance(commands, list), 'Commands must be a list of strings'
        assert len(commands) > 0, 'Empty list of commands'
        for command in commands:
            assert isinstance(command, str), 'Command must be a string'

        def wrapper(func: DecoratedCallable) -> ChatMessageHandler1:
            handler = ChatMessageHandler1(commands=commands, function=func)
            self._message_handlers.append(handler)
            return handler

        return wrapper

    def sender(self) -> Callable[[AsyncSenderFunction], AsyncSenderFunction]:
        def wrapper(func: AsyncSenderFunction) -> AsyncSenderFunction:
            self._sender_func = func
            return func

        return wrapper

    def default_handler(self) -> DecoratedCallable:
        def wrapper(func: DecoratedCallable) -> ChatMessageHandler1:
            self._default_handler_func = func
            return func

        return wrapper

    def overridden_handler(self, message: str, chat: Chat, all_deps: dict[str, Any]) -> Coroutine:
        return handle_message(message, chat, self._compiled_chat_commands, self._default_handler_func, all_deps)

    def before_start(self) -> None:
        super().before_start()
        # TODO: do assert, check if listener_func is exist in self
        self._compiled_chat_commands = compile_chat_commands(self._message_handlers)


class TelegramBot(ChatBot):
    pass


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
