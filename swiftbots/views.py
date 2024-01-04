import aiohttp
import asyncio

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

    async def soft_close_async(self):
        await self.logger.report_async(f'Bot {self.bot.name} was exited')


class ChatView(IChatView, BasicView, ABC):

    default_message_handler_class = ChatMessageHandler

    async def reply_async(self, message: str, context: 'IContext', data: dict = None) -> dict:
        return await self.send_async(message, context['sender'], data)

    async def error_async(self, context: 'IContext'):
        """
        Inform user there is internal error.
        :param context: context with `sender` field
        """
        await self.logger.info_async(f'Error in view. Context: {context}')
        await self.reply_async(self.error_message, context)

    async def unknown_command_async(self, context: 'IContext'):
        """
        If user sends some unknown shit, then needed say him about that
        :param context: context with `sender` and `messages` fields
        """
        await self.logger.info_async(f'User sent unknown command. Context:\n{context}')
        await self.reply_async(self.unknown_error_message, context)

    async def refuse_async(self, context: 'IContext'):
        """
        If user can't use it, then he must be aware.
        :param context: context with `sender` and `messages` fields
        """
        await self.logger.info_async(f'Forbidden. Context:\n{context}')
        await self.reply_async(self.refuse_message, context)

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
    _http_session: aiohttp.client.ClientSession = None
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
        if self._http_session is None or self._http_session.closed:
            self._http_session = aiohttp.ClientSession()

        if not self.__greeting_disabled and self._admin is not None:
            await self.send_async(f'{self.bot.name} is started!', self._admin)

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

    async def fetch_async(self, method: str, data: dict, headers: dict = None) -> dict | None:
        response = await self._http_session.post(f'https://api.telegram.org/bot{self.__token}/{method}',
                                                 json=data, headers=headers)
        answer = await response.json()
        if not answer['ok']:
            await self.__handle_error_async(answer)
            return None
        return answer

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

    async def delete_message_async(self, message_id, context: 'ITelegramView.Context', data: dict = None) -> dict:
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

    def disable_greeting(self) -> None:
        self.__greeting_disabled = True

    async def soft_close_async(self):
        await self.logger.report_async(f'Bot {self.bot.name} was exited')
        if self._http_session is not None:
            await self._http_session.close()
            self._http_session = None

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
    _http_session: aiohttp.ClientSession = None
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
        if self._http_session is None or self._http_session.closed:
            self._http_session = aiohttp.ClientSession()

        if not self.__greeting_disabled and self._admin is not None:
            await self.send_async(f'{self.bot.name} is started!', self._admin)

        try:
            async for update in self.__get_updates_async():
                pre_context = await self._deconstruct_message_async(update)
                if pre_context:
                    yield pre_context

        except aiohttp.ServerConnectionError:
            await self._handle_server_connection_error_async()
        # except Exception as e:
        #     msg = 'Unhandled:' + '\nAnswer is:\n' + str(update) + '\n' + format_exc()
        #     self._logger.error(msg, update['message']['from']['id'])

    async def fetch_async(self, method: str, data: dict = None,
                          headers: dict = None, query_data: dict = None,
                          ignore_errors=False) -> dict | None:

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
            await self.__handle_error_async(answer)
            return answer
        return answer

    async def send_async(self, message: str, user: int | str, data: dict = None) -> dict:
        """
        :returns: {
                      "response":5
                  }, where response is message id
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

    async def update_message_async(self, message: str, message_id: int, context: 'IContext', data: dict = None) -> dict:
        if data is None:
            data = {}
        data['peer_id'] = context['sender']
        data['message_id'] = message_id
        data['message'] = message
        return await self.fetch_async('messages.edit', data)

    async def send_sticker_async(self, sticker_id: str, context: 'IContext', data: dict = None) -> dict:
        if data is None:
            data = {}
        data['user_id'] = context['sender']
        data['random_id'] = self.get_random_id()
        data['sticker_id'] = sticker_id
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

    async def __get_updates_async(self) -> AsyncGenerator[dict, None]:
        """
        https://dev.vk.com/ru/api/bots-long-poll/getting-started#Подключение
        """
        key, server, ts = await self.__get_long_poll_server_async()

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
                    key, server, ts = await self.__get_long_poll_server_async()
                else:
                    raise Exception("Unknown failed")

    def disable_greeting(self) -> None:
        self.__greeting_disabled = True

    async def soft_close_async(self):
        await self.logger.report_async(f'Bot {self.bot.name} was exited')
        if self._http_session is not None:
            await self._http_session.close()
            self._http_session = None

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
