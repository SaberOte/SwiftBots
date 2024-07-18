import asyncio
import random
from collections.abc import Callable
from typing import Any, AsyncGenerator, Coroutine, Dict, List, Optional, TypeVar, Union, Tuple

import aiohttp

from swiftbots.all_types import (
    ExitBotException,
    ILogger,
    ILoggerFactory,
    IScheduler,
    ITrigger,
    RestartListeningException,
)
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

    async def before_start_async(self) -> None:
        """
        Do something right before the app starts.
        Need to override this method.
        Use it like `super().before_start_async()`.
        """
        # TODO: do assert, check if listener_func is exist in self
        ...

    async def before_close_async(self) -> None:
        ...


class StubBot(Bot):
    """
    This class is used as a stub to allow a bot to run without a listener or a handler.
    """

    def __init__(self,
                 name: Optional[str] = None,
                 bot_logger_factory: Optional[ILoggerFactory] = None,
                 ):
        super().__init__(name=name, bot_logger_factory=bot_logger_factory)
        self.listener_func = self.stub_listener
        self.handler_func = self.stub_handler

    async def stub_listener(self) -> Dict:
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

    def __init__(self,
                 name: Optional[str] = None,
                 bot_logger_factory: Optional[ILoggerFactory] = None,
                 ):
        super().__init__(name=name, bot_logger_factory=bot_logger_factory)
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

    async def before_start_async(self) -> None:
        await super().before_start_async()
        # TODO: do assert, check if listener_func is exist in self
        self._compiled_chat_commands = compile_chat_commands(self._message_handlers)


class TelegramBot(ChatBot):
    __token: str
    __admin: Union[str, int, None]
    __http_session: aiohttp.client.ClientSession
    __first_time_launched = True
    ALLOWED_UPDATES = ["messages"]

    def __init__(self,
                 token: str,
                 admin: Union[str, int, None] = None,
                 name: Optional[str] = None,
                 bot_logger_factory: Optional[ILoggerFactory] = None,
                 greeting_enabled: bool = True,
                 skip_old_updates: bool = True):
        super().__init__(name=name, bot_logger_factory=bot_logger_factory)
        self.__token = token
        self.__admin = admin
        self.__greeting_enabled = greeting_enabled
        self._sender_func = self._send_async
        self.__should_skip_old_updates = skip_old_updates
        self.listener_func = self.telegram_listener

    async def _send_async(self, message: str, user: Union[str, int]) -> Dict:
        messages = [message[i: i + 4096] for i in range(0, len(message), 4096)]
        result = {}
        for msg in messages:
            send_data = {"chat_id": user, "text": msg}
            result = await self.fetch_async("sendMessage", send_data)
        return result

    async def fetch_async(
        self,
        method: str,
        data: Dict,
        headers: Optional[Dict] = None,
        ignore_errors: bool = False,
    ) -> Dict:
        url = f"https://api.telegram.org/bot{self.__token}/{method}"
        response = await self.__http_session.post(url=url, json=data, headers=headers)

        answer = await response.json()

        if not answer["ok"] and not ignore_errors:
            state = await self._handle_error_async(answer)
            if state == 0:  # repeat request
                await asyncio.sleep(4)
                response = await self.__http_session.post(
                    url=url, json=data, headers=headers
                )
                answer = await response.json()
            if not answer["ok"]:
                raise RestartListeningException()
        return answer

    async def telegram_listener(self) -> None:
        while True:
            if self.__greeting_enabled and self.__admin is not None:
                await self._sender_func(f"{self.name} is started!", self.__admin)

            try:
                async for update in self._get_updates_async():
                    data = await self._deconstruct_message_async(update)
                    if data:
                        yield data

            except (aiohttp.ServerConnectionError, aiohttp.ClientConnectorError):
                await self._handle_server_connection_error_async()

    async def _deconstruct_message_async(self, update: Dict) -> Union[Dict, None]:
        update = update["result"][0]
        if "message" in update and "text" in update["message"]:
            message = update["message"]
            text = message["text"]
            sender = message["from"]["id"]
            username = (
                message["from"]["username"]
                if "username" in message["from"]
                else "no username"
            )
            await self.logger.info_async(
                f"Came message from '{sender}' ({username}): '{text}'"
            )
            return {
                "message": text,
                "sender": sender,
                "username": username,
                "raw_update": update
            }
        else:
            await self.logger.error_async("Unknown message type:\n" + str(update))
        return None

    async def _handle_server_connection_error_async(self) -> None:
        await self.logger.info_async(
            f"Connection ERROR in {self.name}. Sleep 5 seconds"
        )
        await asyncio.sleep(5)

    async def _get_updates_async(self) -> AsyncGenerator[dict, None]:
        """
        Long Polling: Telegram BOT API https://core.telegram.org/bots/api
        """
        timeout = 1000
        data = {"timeout": timeout, "limit": 1, "allowed_updates": self.ALLOWED_UPDATES}
        if self.__first_time_launched or self.__should_skip_old_updates:
            self.first_time_launched = False
            data["offset"] = await self._skip_old_updates_async()
        while True:
            ans = await self.fetch_async("getUpdates", data, ignore_errors=True)
            if not ans["ok"]:
                state = await self._handle_error_async(ans)
                if state == 0:
                    await asyncio.sleep(5)
                    continue
                else:
                    raise ExitBotException(
                        f"Error {ans} while recieving long polling server"
                    )
            if len(ans["result"]) != 0:
                data["offset"] = ans["result"][0]["update_id"] + 1
                yield ans

    async def _handle_error_async(self, error: dict) -> int:
        """
        https://core.telegram.org/api/errors
        :returns: whether code should continue executing after the error.
        -1 if bot should be exited. Raises BaseException this case
        0 if it should just repeat request.
        1 if it's better to finish this request. The same subsequent requests will fail too.
        """
        error_code: int = error["error_code"]
        error_msg: str = error["description"]
        msg = f"Error {error_code} from TG API: {error_msg}"
        # notify administrator and repeat request
        if error_code in (400, 403, 404, 406, 500, 303):
            await self.logger.error_async(msg)
            return 1
        # too many requests (flood)
        elif error_code == 420:
            await self.logger.error_async(
                f"{self.name} reached Flood error. Fix the code"
            )
            await asyncio.sleep(10)
            return 0
        # unauthorized
        elif error_code == 401:
            await self.logger.critical_async(msg)
            raise ExitBotException()
        elif error_code == 409:
            msg = (
                "Error code 409. Another telegram instance is working. "
                "Shutting down this instance"
            )
            await self.logger.critical_async(msg)
            raise ExitBotException(msg)
        else:
            await self.logger.error_async("Unknown error. Add code" + msg)
            return 1

    async def _skip_old_updates_async(self) -> int:
        data = {"timeout": 0, "limit": 1, "offset": -1}
        ans = await self.fetch_async("getUpdates", data)
        result = ans["result"]
        if len(result) > 0:
            return result[0]["update_id"] + 1
        return -1

    async def before_close_async(self) -> None:
        await super().before_close_async()
        if not self.__http_session.closed:
            await self.__http_session.close()

    async def before_start_async(self) -> None:
        await super().before_start_async()
        self.__http_session = aiohttp.ClientSession()


class VkontakteBot(ChatBot):
    _group_id: int
    __default_headers: dict
    __admin: Union[int, None]
    __http_session: aiohttp.client.ClientSession
    __first_time_launched = True
    ALLOWED_UPDATES = ["messages"]

    def __init__(self,
                 token: str,
                 group_id: Union[int, str],
                 admin: Union[str, int, None] = None,
                 name: Optional[str] = None,
                 bot_logger_factory: Optional[ILoggerFactory] = None,
                 greeting_enabled: bool = True,
                 skip_old_updates: bool = True,
                 api_version: str = "5.199"):
        super().__init__(name=name, bot_logger_factory=bot_logger_factory)
        self.__token = token
        self._group_id = int(group_id)
        self.__admin = int(admin) if admin is not None else None
        self.__greeting_enabled = greeting_enabled
        self._sender_func = self._send_async
        self.__should_skip_old_updates = skip_old_updates
        self.listener_func = self.vk_listener
        self.__API_VERSION = api_version
        self.__default_headers = {"Authorization": f"Bearer {token}"}

    async def _send_async(self, message: str, user: Union[int, str]) -> dict:
        """
        :returns: {
                      "response": 5
                  }, where response is a message id
        """
        # if the message out of 4096 letters, split it on chunks
        messages = [message[i: i + 4096] for i in range(0, len(message), 4096)]
        result = {}
        for msg in messages:
            send_data = {
                "user_id": int(user),
                "message": msg,
                "random_id": self.get_random_id(),
            }
            result = await self.fetch_async("messages.send", send_data)
        return result

    async def fetch_async(
            self,
            method: str,
            data: Optional[Dict] = None,
            headers: Optional[Dict] = None,
            query_data: Optional[Dict] = None,
            ignore_errors: bool = False,
    ) -> Dict:
        args = (
            "".join([f"{name}={value}&" for name, value in query_data.items()])
            if query_data
            else ""
        )
        url = (
            f"https://api.vk.com/method/"
            f"{method}?"
            f"{args}"
            f"v={self.__API_VERSION}"
        )

        request_headers = self.__default_headers.copy()
        if headers is not None:
            request_headers.update(headers)

        response = await self.__http_session.post(
            url=url, data=data, headers=request_headers
        )

        answer = await response.json()
        if "error" in answer and not ignore_errors:
            state = await self._handle_error_async(answer)
            if state == 0:  # repeat request
                await asyncio.sleep(5)
                response = await self.__http_session.post(
                    url=url, data=data, headers=request_headers
                )
                answer = await response.json()
            if "error" in answer:
                await self.logger.info_async("Error and Restart Listener invoked: " + str(answer))
                raise RestartListeningException()
        return answer

    async def vk_listener(self) -> None:
        while True:
            if self.__greeting_enabled and self.__admin is not None:
                await self._sender_func(f"{self.name} is started!", self.__admin)

            try:
                async for update in self._get_updates_async():
                    data = await self._deconstruct_message_async(update)
                    if data:
                        yield data

            except (aiohttp.ServerConnectionError, aiohttp.ClientConnectorError):
                await self._handle_server_connection_error_async()

    async def _deconstruct_message_async(self, update: dict) -> Dict:
        message = update["object"]["message"]
        text: str = message["text"]
        sender: int = message["from_id"]
        message_id: int = message["id"]
        await self.logger.debug_async(f"Came message from '{sender}': '{text}'")
        return {
            "message": text,
            "sender": sender,
            "message_id": message_id
        }

    async def _handle_server_connection_error_async(self) -> None:
        await self.logger.info_async(
            f"Connection ERROR in {self.name}. Sleep 5 seconds"
        )
        await asyncio.sleep(5)

    async def _get_long_poll_server_async(self) -> Tuple[str, str, str]:
        """
        https://dev.vk.com/ru/api/bots-long-poll/getting-started#Подключение
        """
        data = {"group_id": self._group_id}
        result = await self.fetch_async("groups.getLongPollServer", query_data=data)
        if "error" in result:
            state = await self._handle_error_async(result)
            if state == 0:
                await asyncio.sleep(5)
                return await self._get_long_poll_server_async()
            else:
                raise ExitBotException(
                    f"An error {result} occured while receiving a long polling server"
                )
        key = result["response"]["key"]
        server = result["response"]["server"]
        ts = result["response"]["ts"]
        return key, server, ts

    async def _get_updates_async(self) -> AsyncGenerator[dict, None]:
        """
        https://dev.vk.com/ru/api/bots-long-poll/getting-started#Подключение
        """
        key, server, ts = await self._get_long_poll_server_async()

        timeout = "25"
        while True:
            url = f"{server}?act=a_check&key={key}&ts={ts}&wait={timeout}"
            ans = await self.__http_session.post(url=url)
            result = await ans.json()
            if "updates" in result:
                updates = result["updates"]
                if len(updates) != 0:
                    ts = result["ts"]
                    for update in updates:
                        yield update
            else:
                failed = result["failed"]
                if failed == 1:
                    ts = result["ts"]
                elif failed in [2, 3]:
                    key, server, ts = await self._get_long_poll_server_async()
                else:
                    raise Exception("Unknown failed")

    async def _handle_error_async(self, error: dict) -> int:
        """
        https://dev.vk.com/ru/reference/errors
        :returns: whether code should continue executing after the error.
        -1 if bot should be exited. Never returns, raises BaseException
        0 if it should just repeat request.
        1 if it's better to finish this request. The same subsequent requests will fail too.
        """
        error_code: int = error["error"]["error_code"]
        error_msg: str = error["error"]["error_msg"]
        msg = f"Error {error_code} from VK API: {error_msg}"
        # just need to wait and repeat request
        if error_code in (1, 10):
            await self.logger.error_async(msg)
            return 0
        # notify administrator
        elif error_code in (
            3,
            8,
            9,
            14,
            15,
            16,
            17,
            18,
            23,
            24,
            29,
            30,
            113,
            150,
            200,
            201,
            203,
            300,
            500,
            600,
            603,
        ):
            await self.logger.error_async(msg)
            return 1
        # too many requests
        elif error_code == 6:
            await self.logger.error_async(
                f"{self.name} reached too many requests error. Fix the code"
            )
            await asyncio.sleep(10)
            return 0
        # unforgivable errors
        elif error_code in (2, 4, 5, 7, 11, 20, 21, 27, 28, 100, 101):
            await self.logger.critical_async(msg)
            raise ExitBotException(msg)
        else:
            await self.logger.critical_async(
                "Unknown error codes in code for VK! Error:" + msg
            )
            return 1

    @staticmethod
    def get_random_id() -> int:
        return random.randint(-(2 ** 31), 2 ** 31)

    async def before_close_async(self) -> None:
        await super().before_close_async()
        if not self.__http_session.closed:
            await self.__http_session.close()

    async def before_start_async(self) -> None:
        await super().before_start_async()
        self.__http_session = aiohttp.ClientSession()


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
