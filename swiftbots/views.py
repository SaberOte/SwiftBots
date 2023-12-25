import aiohttp
import asyncio

from abc import ABC
from typing import Callable, Optional, TYPE_CHECKING, AsyncGenerator

from swiftbots.types import ILogger, IBasicView, IChatView, ITelegramView
from swiftbots.message_handlers import BasicMessageHandler, ChatMessageHandler

if TYPE_CHECKING:
    from swiftbots.bots import Bot


class BasicView(IBasicView, ABC):

    _default_message_handler_class = BasicMessageHandler

    def init(self, bot: 'Bot', logger: 'ILogger') -> None:
        self._bot = bot
        self._logger = logger

    def _close(self):
        pass

    @property
    def _logger(self) -> ILogger:
        return self.__logger

    @_logger.setter
    def _logger(self, logger: ILogger) -> None:
        assert isinstance(logger, ILogger)
        self.__logger = logger

    @property
    def _listener(self) -> Callable:
        return self.listen_async if self._overriden_listener is None else self._overriden_listener

    @_listener.setter
    def _listener(self, listener: Callable) -> None:
        assert isinstance(listener, Callable)
        self.__overriden_listener = listener

    @property
    def _bot(self) -> 'Bot':
        return self.__bot

    @_bot.setter
    def _bot(self, bot: 'Bot') -> None:
        self.__bot = bot


class ChatView(IChatView, BasicView, ABC):

    _default_message_handler_class = ChatMessageHandler

    async def error_async(self, context: dict):
        """
        Inform user there is internal error.
        :param context: context with `sender` and `messages` fields
        """
        await self.send_async(self.error_message, context)

    async def unknown_command_async(self, context: dict):
        """
        If user sends some unknown shit, then needed say him about that
        :param context: context with `sender` and `messages` fields
        """
        self._logger.info(f'User sends unknown command. Context:\n{context}')
        await self.send_async(self.unknown_error_message, context)

    async def refuse_async(self, context: dict):
        """
        If user can't use it, then he must be aware.
        :param context: context with `sender` and `messages` fields
        """
        self._logger.info(f'Forbidden. Context:\n{context}')
        await self.send_async(self.refuse_message, context)


class TelegramView(ITelegramView, ChatView, ABC):

    __token: str
    _admin: Optional[str]
    __first_time_launched = True
    __should_skip_old_updates: bool
    __greeting_disabled = False
    _http_session = None
    ALLOWED_UPDATES = ["messages"]

    def __init__(self, token: str, admin: str = None, skip_old_updates: bool = True):
        """
        :param token: Auth token of bot
        :param admin: admin id to send reports or errors. Optional
        :param skip_old_updates: whether should bot skip all updates from users after errors.
        """
        self.__token = token
        self._admin = admin
        self.__should_skip_old_updates = skip_old_updates

    async def listen_async(self) -> AsyncGenerator['ITelegramView.PreContext', None]:
        self._http_session = aiohttp.ClientSession()

        if not self.__greeting_disabled:
            await self.report_async(f'{self._bot.name} is started')

        while True:
            try:
                async for update in self._get_updates_async():
                    pre_context = self._deconstruct_message(update)
                    if pre_context:
                        yield pre_context

            except aiohttp.ServerConnectionError:
                await self._handle_server_connection_error_async()
            # except Exception as e:
            #     msg = 'Unhandled:' + '\nAnswer is:\n' + str(update) + '\n' + format_exc()
            #     self._logger.error(msg, update['message']['from']['id'])

    async def fetch_async(self, method: str, data: dict) -> dict | None:
        response = await self._http_session.post(f'https://api.telegram.org/bot{self.__token}/{method}', json=data)
        answer = await response.json()
        if not answer['ok']:
            await self.__handle_error_async(answer)
            return None
        return answer

    async def update_message_async(self, data: dict) -> dict:
        return await self.fetch_async('editMessageText', data)

    async def send_async(self, message: str, context: 'ITelegramView.Context') -> dict:
        data = {
            "chat_id": context.sender,
            "text": message
        }
        return await self.fetch_async('sendMessage', data)

    async def report_async(self, message: str) -> dict | None:
        if not self._admin:
            self._logger.error(f'No admin id set. Impossible to report the message:\n{message}')
            return None
        data = {
            "chat_id": self._admin,
            "text": message
        }
        return await self.custom_send_async(data)

    async def custom_send_async(self, data: dict) -> dict:
        self._logger.info(f"""Sent {data["chat_id"]}:\n'{data["text"]}'""")
        return await self.fetch_async('sendMessage', data)

    async def delete_message_async(self, message_id, context: 'ITelegramView.Context') -> dict:
        data = {
            "chat_id": context.sender,
            "message_id": message_id
        }
        return await self.fetch_async('deleteMessage', data)

    def disable_greeting(self) -> None:
        self.__greeting_disabled = True

    async def _close_async(self):
        await self._http_session.close()

    async def _handle_server_connection_error_async(self) -> None:
        self._logger.info('Connection ERROR in base_telegram_view.py. Sleep 5 seconds')
        await asyncio.sleep(5)

    def _deconstruct_message(self, update: dict) -> Optional['ITelegramView.PreContext']:
        update = update['result'][0]
        if 'message' in update and 'text' in update['message']:
            message = update['message']
            text = message['text']
            sender = message['from']['id']
            username = message['from']['username'] if 'username' in message['from'] else 'no username'
            self._logger.info(f"Came message from '{sender}' ({username}): '{text}'")
            return self.PreContext(text, sender, username)
        else:
            self._logger.error('Unknown message type:\n', str(update))

    async def _get_updates_async(self) -> AsyncGenerator[dict, None]:
        """
        Long Polling: Telegram BOT API https://core.telegram.org/bots/api
        """
        timeout = 1000
        data = {
            "timeout": timeout,
            "limit": 1,
            "allowed_updates": self.ALLOWED_UPDATES
        }
        if self.__first_time_launched or self.__skip_old_updates_async:
            self.first_time_launched = False
            data['offset'] = await self.__skip_old_updates_async()
        while True:
            ans = await self.fetch_async('getUpdates', data)
            if len(ans['result']) != 0:
                data['offset'] = ans['result'][0]['update_id'] + 1
                yield ans

    async def __handle_error_async(self, error: dict) -> None:
        if error['error_code'] == 409:
            self._logger.critical('Error code 409. Another telegram instance is working. Shutting down this instance')
            await self._bot.shutdown_bot_async()
            # for i in range(2):
            #     time.sleep(1)
            # os.kill(os.getpid(), signal.SIGKILL)
        self.__logger.error(f"Error {error['error_code']} from TG API: {error['description']}")

    async def __skip_old_updates_async(self):
        data = {
            "timeout": 0,
            "limit": 1,
            "offset": -1
        }
        ans = await self.fetch_async('getUpdates', data)
        result = ans['result']
        if len(result) > 0:
            return result[0]['update_id'] + 1
        return -1


"""
class VkontakteView(ChatView):
    pass
"""
