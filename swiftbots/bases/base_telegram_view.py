import aiohttp
import time
import signal
import os
from abc import ABC
from traceback import format_exc
from swiftbots.bases.base_chat_view import BaseChatView, ChatViewContext


class TGViewContext(ChatViewContext):
    """
    FIELDS:
    platform: str
    username: str
    message: str
    sender: str
    """
    def __init__(self, message: str, sender: str, username: str):
        super().__init__(message, sender)
        self.platform = 'telegram'
        self.username = username


class BaseTelegramView(BaseChatView, ABC):
    token: str
    admin: str
    first_time_launched = True
    skip_old_updates = False
    http_session = aiohttp.ClientSession()

    async def fetch(self, method: str, data: dict) -> dict:
        response = await self.http_session.post(f'https://api.telegram.org/bot{self.token}/{method}', json=data)
        answer = await response.json()
        if not answer['ok']:
            self._handle_error(answer)
        return answer

    async def update_message(self, data: dict) -> dict:
        """
        Updating the message
        :param data: should contain at least "text", "message_id", "chat_id"
        """
        return await self.fetch('editMessageText', data)

    async def send(self, message: str, chat_id) -> dict:
        data = {
            "chat_id": chat_id,
            "text": message
        }
        return await self.fetch('sendMessage', data)

    async def custom_send(self, data: dict) -> dict:
        """
        Standard send provides only message and chat_id arguments.
        This method can contain any fields in data
        :param data:
        """
        print(f"""Replied {data["chat_id"]}:\n'{data["text"]}'""")
        return await self.fetch('sendMessage', data)

    async def delete_message(self, message_id, chat_id):
        data = {
            "chat_id": chat_id,
            "message_id": message_id
        }
        return await self.fetch('deleteMessage', data)

    def _handle_error(self, error):
        if error['error_code'] == 409:
            for i in range(2):
                self.report(str(i))
                time.sleep(1)
            os.kill(os.getpid(), signal.SIGKILL)
        raise Exception(f"Error {error['error_code']} from TG API: {error['description']}")

    async def __skip_old_updates(self):
        data = {
            "timeout": 0,
            "limit": 1,
            "offset": -1
        }
        ans = await self.fetch('getUpdates', data)
        result = ans['result']
        if len(result) > 0:
            return result[0]['update_id'] + 1
        return -1

    async def _get_updates(self):
        timeout = 1000
        data = {
            "timeout": timeout,
            "limit": 1,
            "allowed_updates": ["messages"]
        }
        if self.first_time_launched or self.skip_old_updates:
            self.first_time_launched = False
            data['offset'] = await self.__skip_old_updates()
        while 1:
            ans = await self.fetch('getUpdates', data)
            if len(ans['result']) != 0:
                data['offset'] = ans['result'][0]['update_id'] + 1
                yield ans

    async def listen(self):
        """
        Long Polling: Telegram BOT API https://core.telegram.org/bots/api
        """

        if self.admin:
            await self.report(f'{self.get_name()} is started')

        try:
            for update in await self._get_updates():
                try:
                    update = update['result'][0]
                    if 'message' in update and 'text' in update['message']:
                        message = update['message']
                        text = message['text']
                        sender = message['from']['id']
                        username = message['from']['username'] if 'username' in message['from'] else 'no username'
                        print(f"Came message from {sender} ({username}): '{text}'")
                        yield TGViewContext(text, sender, username)
                    else:
                        print('UNHANDLED\n', str(update))
                except Exception:
                    msg = 'Unhandled:' + '\nAnswer is:\n' + str(update) + '\n' + format_exc()
                    await self.error(msg, update['message']['from']['id'])
        except aiohttp.ServerConnectionError:
            print('Connection ERROR in base_telegram_view.py. Sleep 5 seconds')
            reported = 1  # = self.try_report('connection error')
            if reported != 1:
                print('Not reported', reported)
            time.sleep(5)
