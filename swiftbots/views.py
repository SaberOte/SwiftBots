import aiohttp
import asyncio
import random

from abc import ABC
from typing import Optional, TYPE_CHECKING, AsyncGenerator

from swiftbots.types import ILogger, IBasicView, IChatView, ITelegramView, IVkontakteView, IContext
from swiftbots.admin_utils import shutdown_bot_async
from swiftbots.message_handlers import BasicMessageHandler, ChatMessageHandler

if TYPE_CHECKING:
    from swiftbots.bots import Bot


class BasicView(IBasicView, ABC):

    default_message_handler_class = BasicMessageHandler
    __bot: 'Bot'
    __logger: Optional['ILogger']

    def init(self, bot: 'Bot') -> None:
        self.__bot = bot
        self.__logger = bot.logger

    @property
    def logger(self) -> ILogger:
        return self.__logger

    @property
    def bot(self) -> 'Bot':
        return self.__bot

    async def _close_async(self):
        pass


class ChatView(IChatView, BasicView, ABC):

    default_message_handler_class = ChatMessageHandler

    async def error_async(self, context: 'IContext'):
        """
        Inform user there is internal error.
        :param context: context with `sender` and `messages` fields
        """
        await self.logger.info_async(f'Error in view. Context: {context}')
        await self.send_async(self.error_message, context)

    async def unknown_command_async(self, context: 'IContext'):
        """
        If user sends some unknown shit, then needed say him about that
        :param context: context with `sender` and `messages` fields
        """
        await self.logger.info_async(f'User sent unknown command. Context:\n{context}')
        await self.send_async(self.unknown_error_message, context)

    async def refuse_async(self, context: 'IContext'):
        """
        If user can't use it, then he must be aware.
        :param context: context with `sender` and `messages` fields
        """
        await self.logger.info_async(f'Forbidden. Context:\n{context}')
        await self.send_async(self.refuse_message, context)

    async def is_admin_async(self, user) -> bool:
        if self._admin is None:
            await self.logger.error_async(f"No `_admin` property is set for view {self.bot.name}")
            return False
        return str(self._admin) == str(user)


class TelegramView(ITelegramView, ChatView, ABC):

    __token: str
    __first_time_launched = True
    __should_skip_old_updates: bool
    __greeting_disabled = False
    http_session = None
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
        self.http_session = aiohttp.ClientSession()

        if not self.__greeting_disabled and self._admin is not None:
            await self.custom_send_async({'chat_id': self._admin, 'text': f'{self.bot.name} is started!'})

        while True:
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

    async def fetch_async(self, method: str, data: dict) -> dict | None:
        response = await self.http_session.post(f'https://api.telegram.org/bot{self.__token}/{method}', json=data)
        answer = await response.json()
        if not answer['ok']:
            await self.__handle_error_async(answer)
            return None
        return answer

    async def update_message_async(self, data: dict) -> dict:
        return await self.fetch_async('editMessageText', data)

    async def send_async(self, message: str, context: 'IContext') -> dict:
        data = {
            "chat_id": context['sender'],
            "text": message
        }
        return await self.fetch_async('sendMessage', data)

    async def custom_send_async(self, data: dict) -> dict:
        await self.logger.info_async(f"""Sent {data["chat_id"]}:\n'{data["text"]}'""")
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
        await self.http_session.close()

    async def _handle_server_connection_error_async(self) -> None:
        await self.logger.info_async(f'Connection ERROR in {self.bot.name}. Sleep 5 seconds')
        await asyncio.sleep(5)

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
            await shutdown_bot_async()
            await self.logger.critical_async('Error code 409. Another telegram instance is working. '
                                             'Shutting down this instance')
        await self.logger.error_async(f"Error {error['error_code']} from TG API: {error['description']}")

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


class VkontakteView(IVkontakteView, ChatView, ABC):

    _group_id: int
    _first_time_launched = True
    _http_session: aiohttp.ClientSession
    __API_VERSION = '5.199'
    __default_headers: dict
    __greeting_disabled: bool = False

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

    async def listen_async(self):
        self._http_session = aiohttp.ClientSession()
        key, server, ts = await self.__get_long_poll_server_async()

        if not self.__greeting_disabled and self._admin is not None:
            await self.custom_send_async({'message': f'{self.bot.name} is started!', 'user_id': self._admin})

        try:
            async for update in self.__get_updates_async(key, server, ts):
                pre_context = await self._deconstruct_message_async(update)
                if pre_context:
                    yield pre_context

        except aiohttp.ServerConnectionError:
            await self._handle_server_connection_error_async()
        # except Exception as e:
        #     msg = 'Unhandled:' + '\nAnswer is:\n' + str(update) + '\n' + format_exc()
        #     self._logger.error(msg, update['message']['from']['id'])

    async def fetch_async(self, method: str, data: dict = None,
                          headers: dict = None, query_data: dict = None) -> dict | None:

        args = ''.join([f"{name}={value}&" for name, value in query_data.items()]) if query_data else ''
        url = (f'https://api.vk.com/method/'
               f'{method}?'
               f'{args}'
               f'v={self.__API_VERSION}')

        if headers is None:
            headers = self.__default_headers
        else:
            headers.update(self.__default_headers)

        response = await self._http_session.post(url=url, data=data, headers=headers)

        answer = await response.json()
        if 'error' in answer:
            await self.__handle_error_async(answer)
            return answer
        return answer

    async def send_async(self, message: str, context: 'IContext') -> dict:
        # if message out of 9000 letters, split it on chunks
        messages = [message[i:i + 9000] for i in range(0, len(message), 9000)]
        result = {}
        for msg in messages:
            data = {
                'user_id': context['sender'],
                'message': msg,
                'random_id': random.randint(-2 ** 31, 2 ** 31)
            }
            result = await self.fetch_async('messages.send', data)
        return result

    async def custom_send_async(self, data: dict) -> dict:
        await self.logger.info_async(f"""Sent {data["user_id"]}:\n'{data["message"]}'""")
        if 'random_id' not in data:
            data['random_id'] = random.randint(-2 ** 31, 2 ** 31)
        return await self.fetch_async('messages.send', data)

    async def __handle_error_async(self, error: dict) -> None:
        error_code: int = error['error']['error_code']
        error_msg: str = error['error']['error_msg']
        msg = f"Error {error_code} from VK API: {error_msg}"
        if error_code == 100:
            await shutdown_bot_async()
            await self.logger.critical_async(msg)
        await self.logger.error_async(msg)

    async def __get_long_poll_server_async(self) -> tuple[str, str, str]:
        """
        https://dev.vk.com/ru/api/bots-long-poll/getting-started#Подключение
        """
        data = {'group_id': self._group_id}
        result = await self.fetch_async('groups.getLongPollServer', query_data=data)
        key = result['response']['key']
        server = result['response']['server']
        ts = result['response']['ts']
        return key, server, ts

    async def __get_updates_async(self, key: str, server: str, ts: str) -> AsyncGenerator[dict, None]:
        """
        https://dev.vk.com/ru/api/bots-long-poll/getting-started#Подключение
        """
        timeout = '25'
        while True:
            url = f"{server}?act=a_check&key={key}&ts={ts}&wait={timeout}"
            ans = await self._http_session.post(url=url)
            result = await ans.json()
            updates = result['updates']
            if len(updates) != 0:
                ts = result['ts']
                for update in updates:
                    yield update

    def disable_greeting(self) -> None:
        self.__greeting_disabled = True

    async def _close_async(self):
        await self._http_session.close()

    async def _deconstruct_message_async(self, update: dict) -> Optional['ITelegramView.PreContext']:

        message = update['object']['message']
        text: str = message['text']
        sender: int = message['from_id']
        message_id: int = message['id']
        await self.logger.info_async(f"Came message from '{sender}': '{text}'")
        return self.PreContext(message=text, sender=sender, message_id=message_id)

    async def _handle_server_connection_error_async(self) -> None:
        await self.logger.info_async(f'Connection ERROR in {self.bot.name}. Sleep 5 seconds')
        await asyncio.sleep(5)
