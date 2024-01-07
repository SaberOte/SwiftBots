import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Optional

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from swiftbots.message_handlers import BasicMessageHandler, ChatMessageHandler
from swiftbots.types import (
    ExitBotException,
    IBasicView,
    IChatView,
    IContext,
    ILogger,
    ITelegramView,
    IVkontakteView,
    RestartListeningException,
)

if TYPE_CHECKING:
    from swiftbots.bots import Bot


class BasicView(IBasicView, ABC):

    default_message_handler_class = BasicMessageHandler
    __bot: 'Bot'
    __logger: Optional['ILogger']

    def init(self, bot: 'Bot', db_session_maker: async_sessionmaker[AsyncSession] | None) -> None:
        self.__bot = bot
        self.__logger = bot.logger
        self._set_db_session_maker(db_session_maker)

    @property
    def logger(self) -> ILogger:
        return self.__logger

    @property
    def bot(self) -> 'Bot':
        return self.__bot

    async def soft_close_async(self) -> None:
        await self.logger.report_async(f'Bot {self.bot.name} was exited')


class ChatView(IChatView, BasicView, ABC):

    default_message_handler_class = ChatMessageHandler

    async def reply_async(self, message: str, context: 'IContext', data: dict = None) -> dict:
        return await self.send_async(message, context['sender'], data)

    async def error_async(self, context: 'IContext') -> dict:
        """
        Inform user there is internal error.
        :param context: context with `sender` field
        """
        await self.logger.info_async(f'Error in view. Context: {context}')
        return await self.reply_async(self.error_message, context)

    async def unknown_command_async(self, context: 'IContext') -> dict:
        """
        if a user sends some unknown shit, then needed say him about that
        :param context: context with `sender` and `messages` fields
        """
        await self.logger.info_async(f'User sent unknown command. Context:\n{context}')
        return await self.reply_async(self.unknown_error_message, context)

    async def refuse_async(self, context: 'IContext') -> dict:
        """
        if a user can't use it, then it must be aware.
        :param context: context with `sender` and `messages` fields
        """
        await self.logger.info_async(f'Forbidden. Context:\n{context}')
        return await self.reply_async(self.refuse_message, context)

    async def is_admin_async(self, user: str | int) -> bool:
        if self._admin is None:
            await self.logger.error_async(f"No `_admin` property is set for view {self.bot.name}")
            return False
        return str(self._admin) == str(user)


class AbstractInternetChatView(IChatView, ABC):
    _http_session: aiohttp.client.ClientSession
    __greeting_disabled = False

    def disable_greeting(self) -> None:
        self.__greeting_disabled = True

    async def listen_async(self) -> AsyncGenerator['IChatView.PreContext', None]:
        await self._ensure_http_session_created()

        if not self.__greeting_disabled and self._admin is not None:
            await self.send_async(f'{self.bot.name} is started!', self._admin)

        try:
            async for update in self._get_updates_async():
                pre_context = await self._deconstruct_message_async(update)
                if pre_context:
                    yield pre_context

        except aiohttp.ServerConnectionError:
            await self._handle_server_connection_error_async()
        # except Exception as e:
        #     msg = 'Unhandled:' + '\nAnswer is:\n' + str(update) + '\n' + format_exc()
        #     self._logger.error(msg, update['message']['from']['id'])

    async def soft_close_async(self) -> None:
        await self.logger.report_async(f'Bot {self.bot.name} was exited')
        await self._ensure_http_session_closed()

    async def _handle_server_connection_error_async(self) -> None:
        await self.logger.info_async(f'Connection ERROR in {self.bot.name}. Sleep 5 seconds')
        await asyncio.sleep(5)

    @abstractmethod
    async def _get_updates_async(self) -> AsyncGenerator[dict, None]:
        yield {}  # py charm pisses off without this
        raise NotImplementedError()

    @abstractmethod
    async def _deconstruct_message_async(self, update: dict) -> Optional['IChatView.PreContext']:
        raise NotImplementedError()

    async def _ensure_http_session_created(self) -> None:
        if '_http_session' not in vars(self):
            self._http_session = aiohttp.ClientSession()

    async def _ensure_http_session_closed(self) -> None:
        if '_http_session' in vars(self) and not self._http_session.closed:
            await self._http_session.close()


class TelegramView(ITelegramView, ChatView, AbstractInternetChatView, ABC):
    __token: str
    __first_time_launched = True
    __should_skip_old_updates: bool
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

    async def fetch_async(self, method: str, data: dict, headers: dict = None,
                          ignore_errors: bool = False) -> dict | None:
        url = f'https://api.telegram.org/bot{self.__token}/{method}'
        response = await self._http_session.post(url=url, json=data, headers=headers)

        answer = await response.json()

        if not answer['ok'] and not ignore_errors:
            state = await self._handle_error_async(answer)
            if state == 0:  # repeat request
                await asyncio.sleep(4)
                response = await self._http_session.post(url=url, json=data, headers=headers)
                answer = await response.json()
            if not answer['ok']:
                raise RestartListeningException()
        return answer
    """ TODO: совместить 2 метода
    async def fetch_async(self, method: str, data: dict | None = None,
                          headers: dict | None = None, query_data: dict | None = None,
                          ignore_errors: bool = False) -> dict:

        args = ''.join([f"{name}={value}&" for name, value in query_data.items()]) if query_data else ''
        url = (f'https://api.vk.com/method/'
               f'{method}?'
               f'{args}'
               f'v={self.__API_VERSION}')

        request_headers = self.__default_headers.copy()
        if headers is not None:
            request_headers.update(headers)

        response = await self._http_session.post(url=url, data=data, headers=request_headers)

        answer = await response.json()
        if 'error' in answer and not ignore_errors:
            state = await self._handle_error_async(answer)
            if state == 0:  # repeat request
                await asyncio.sleep(5)
                response = await self._http_session.post(url=url, data=data, headers=request_headers)
                answer = await response.json()
            if 'error' in answer:
                raise RestartListeningException()
        return answer"""

    async def update_message_async(self, text: str, message_id: int, context: 'IContext', data: dict = None) -> dict:
        if data is None:
            data = {}
        data['text'] = text
        data['message_id'] = message_id
        data['chat_id'] = context['sender']
        return await self.fetch_async('editMessageText', data)

    async def send_async(self, message: str, user: str | int, data: dict = None) -> dict:
        if data is None:
            data = {}

        messages = [message[i:i + 4096] for i in range(0, len(message), 4096)]
        result = {}
        for msg in messages:
            send_data = {
                'chat_id': user,
                'text': msg
            }
            send_data.update(data)
            result = await self.fetch_async('sendMessage', send_data)
        return result

    async def delete_message_async(self, message_id: int, context: 'ITelegramView.Context', data: dict = None) -> dict:
        if data is None:
            data = {}
        data['chat_id'] = context.sender
        data['message_id'] = message_id
        return await self.fetch_async('deleteMessage', data)

    async def send_sticker_async(self, file_id: str, context: 'IContext', data: dict = None) -> dict:
        if data is None:
            data = {}
        data['chat_id'] = context['sender']
        data['sticker'] = file_id
        return await self.fetch_async('sendSticker', data)

    async def _deconstruct_message_async(self, update: dict) -> Optional['ITelegramView.PreContext']:
        update = update['result'][0]
        if 'message' in update and 'text' in update['message']:
            message = update['message']
            text = message['text']
            sender = message['from']['id']
            username = message['from']['username'] if 'username' in message['from'] else 'no username'
            await self.logger.info_async(f"Came message from '{sender}' ({username}): '{text}'")
            return self.PreContext(text, sender, username)
        else:
            await self.logger.error_async('Unknown message type:\n', str(update))

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
        if self.__first_time_launched or self._skip_old_updates_async:
            self.first_time_launched = False
            data['offset'] = await self._skip_old_updates_async()
        while True:
            ans = await self.fetch_async('getUpdates', data, ignore_errors=True)
            if not ans['ok']:
                state = await self._handle_error_async(ans)
                if state == 0:
                    await asyncio.sleep(5)
                    yield self._get_updates_async()
                else:
                    raise ExitBotException(f"Error {ans} while recieving long polling server")
            if len(ans['result']) != 0:
                data['offset'] = ans['result'][0]['update_id'] + 1
                yield ans

    async def _handle_error_async(self, error: dict) -> int:
        """
        https://core.telegram.org/api/errors
        :returns: whether code should continue executing after the error.
        -1 if bot should be exited. Never returns, raises BaseException
        0 if it should just repeat request.
        1 if it's better to finish this request. The same subsequent requests will fail too.
        """
        error_code: int = error['error_code']
        error_msg: str = error['description']
        msg = f"Error {error_code} from TG API: {error_msg}"
        # notify administrator and repeat request
        if error_code in (400, 403, 404, 406, 500, 303):
            await self.logger.error_async(msg)
            return 1
        # too many requests (flood)
        elif error_code == 420:
            await self.logger.error_async(f"{self.bot.name} reached Flood error. Fix the code")
            await asyncio.sleep(10)
            return 0
        # unauthorized
        elif error_code == 401:
            await self.logger.critical_async(msg)
            raise ExitBotException(msg)
        elif error_code == 409:
            msg = ('Error code 409. Another telegram instance is working. '
                   'Shutting down this instance')
            await self.logger.critical_async(msg)
            raise ExitBotException(msg)
        else:
            await self.logger.error_async('Unknown error. Add code' + msg)
            return 1

    async def _skip_old_updates_async(self) -> int:
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


class VkontakteView(IVkontakteView, ChatView, AbstractInternetChatView, ABC):

    _group_id: int
    __API_VERSION = '5.199'
    __default_headers: dict

    def __init__(self, token: str, group_id: int, admin: int = None):
        """
        :param token: Auth token of bot
        :param admin: admin id to send reports or errors. Optional
        """
        self._admin = admin
        self._group_id = group_id
        self.__default_headers = {
            'Authorization': f'Bearer {token}'
        }

    async def fetch_async(self, method: str, data: dict | None = None,
                          headers: dict | None = None, query_data: dict | None = None,
                          ignore_errors: bool = False) -> dict:

        args = ''.join([f"{name}={value}&" for name, value in query_data.items()]) if query_data else ''
        url = (f'https://api.vk.com/method/'
               f'{method}?'
               f'{args}'
               f'v={self.__API_VERSION}')

        request_headers = self.__default_headers.copy()
        if headers is not None:
            request_headers.update(headers)

        response = await self._http_session.post(url=url, data=data, headers=request_headers)

        answer = await response.json()
        if 'error' in answer and not ignore_errors:
            state = await self._handle_error_async(answer)
            if state == 0:  # repeat request
                await asyncio.sleep(5)
                response = await self._http_session.post(url=url, data=data, headers=request_headers)
                answer = await response.json()
            if 'error' in answer:
                raise RestartListeningException()
        return answer

    async def send_async(self, message: str, user: int | str, data: dict | None = None) -> dict:
        """
        :returns: {
                      "response": 5
                  }, where response is a message id
        """
        if data is None:
            data = {}
        # if the message out of 4096 letters, split it on chunks
        messages = [message[i:i + 4096] for i in range(0, len(message), 4096)]
        result = {}
        for msg in messages:
            send_data = {
                'user_id': int(user),
                'message': msg,
                'random_id': self.get_random_id()
            }
            send_data.update(data)
            result = await self.fetch_async('messages.send', send_data)
        return result

    async def update_message_async(self, message: str, message_id: int, context: 'IContext', data: dict | None = None) -> dict:
        if data is None:
            data = {}
        data['peer_id'] = context['sender']
        data['message_id'] = message_id
        data['message'] = message
        return await self.fetch_async('messages.edit', data)

    async def send_sticker_async(self, sticker_id: int, context: 'IContext', data: dict | None = None) -> dict:
        if data is None:
            data = {}
        data['user_id'] = context['sender']
        data['random_id'] = self.get_random_id()
        data['sticker_id'] = sticker_id
        return await self.fetch_async('messages.send', data)

    async def _deconstruct_message_async(self, update: dict) -> 'IChatView.PreContext':
        message = update['object']['message']
        text: str = message['text']
        sender: int = message['from_id']
        message_id: int = message['id']
        await self.logger.info_async(f"Came message from '{sender}': '{text}'")
        return self.PreContext(message=text, sender=sender, message_id=message_id)

    async def _handle_error_async(self, error: dict) -> int:
        """
        https://dev.vk.com/ru/reference/errors
        :returns: whether code should continue executing after the error.
        -1 if bot should be exited. Never returns, raises BaseException
        0 if it should just repeat request.
        1 if it's better to finish this request. The same subsequent requests will fail too.
        """
        error_code: int = error['error']['error_code']
        error_msg: str = error['error']['error_msg']
        msg = f"Error {error_code} from VK API: {error_msg}"
        # just need to wait and repeat request
        if error_code in (1, 10):
            await self.logger.error_async(msg)
            return 0
        # notify administrator
        elif error_code in (3, 8, 9, 14, 15, 16, 17, 18, 23, 24, 29, 30, 113, 150, 200, 201, 203, 300, 500, 600, 603):
            await self.logger.error_async(msg)
            return 1
        # too many requests
        elif error_code == 6:
            await self.logger.error_async(f"{self.bot.name} reached too many requests error. Fix the code")
            await asyncio.sleep(10)
            return 0
        # unforgivable errors
        elif error_code in (2, 4, 5, 7, 11, 20, 21, 27, 28, 100, 101):
            await self.logger.critical_async(msg)
            raise ExitBotException(msg)
        else:
            await self.logger.critical_async('Need no add error codes in code for VK! Error:' + msg)
            return 1

    async def _get_long_poll_server_async(self) -> tuple[str, str, str]:
        """
        https://dev.vk.com/ru/api/bots-long-poll/getting-started#Подключение
        """
        data = {'group_id': self._group_id}
        result = await self.fetch_async('groups.getLongPollServer', query_data=data)
        if 'error' in result:
            state = await self._handle_error_async(result)
            if state == 0:
                await asyncio.sleep(5)
                return await self._get_long_poll_server_async()
            else:
                raise ExitBotException(f"Error {result} while recieving long polling server")
        key = result['response']['key']
        server = result['response']['server']
        ts = result['response']['ts']
        return key, server, ts

    async def _get_updates_async(self) -> AsyncGenerator[dict, None]:
        """
        https://dev.vk.com/ru/api/bots-long-poll/getting-started#Подключение
        """
        key, server, ts = await self._get_long_poll_server_async()

        timeout = '25'
        while True:
            url = f"{server}?act=a_check&key={key}&ts={ts}&wait={timeout}"
            ans = await self._http_session.post(url=url)
            result = await ans.json()
            if 'updates' in result:
                updates = result['updates']
                if len(updates) != 0:
                    ts = result['ts']
                    for update in updates:
                        yield update
            else:
                failed = result['failed']
                if failed == 1:
                    ts = result['ts']
                elif failed in [2, 3]:
                    key, server, ts = await self._get_long_poll_server_async()
                else:
                    raise Exception("Unknown failed")
