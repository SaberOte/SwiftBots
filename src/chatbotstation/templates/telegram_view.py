import requests
import time
import signal
import os
from abc import ABC
from traceback import format_exc
from .super_view import SuperView


class TelegramView(SuperView, ABC):
    TOKEN: str
    admin: int
    authentic_style = True

    def post(self, method: str, data: dict) -> dict:
        response = requests.get(f'https://api.telegram.org/bot{self.TOKEN}/{method}', json=data)
        answer = response.json()
        if not answer['ok']:
            self.__handle_error(answer)
        return answer

    def update_message(self, data: dict) -> dict:
        """
        Updating the message
        :param data: should contain at least "text", "message_id", "chat_id"
        """
        return self.post('editMessageText', data)

    def send(self, message: str, chat_id) -> dict:
        data = {
            "chat_id": chat_id,
            "text": message
        }
        return self.post('sendMessage', data)

    def custom_send(self, data: dict) -> dict:
        """
        Standard send provides only message and chat_id properties.
        This method can contain any fields in data
        :param data:
        """
        self.log(f'''Replied "{data['chat_id']}":\n"{data['text']}"''')
        return self.post('sendMessage', data)

    def __handle_error(self, error):
        if error['error_code'] == 409:
            for i in range(2):
                self.report(str(i))
                time.sleep(1)
            os.kill(os.getpid(), signal.SIGKILL)
        raise Exception(f"Error {error['error_code']} from TG API: {error['description']}")

    def __skip_old_updates(self):
        data = {
            "timeout": 0,
            "limit": 1,
            "offset": -1
        }
        ans = self.post('getUpdates', data)
        result = ans['result']
        if len(result) > 0:
            return result[0]['update_id'] + 1
        return -1

    def __get_updates(self):
        timeout = 1000
        offset = self.__skip_old_updates()
        data = {
            "timeout": timeout,
            "limit": 1,
            "offset": offset,
            "allowed_updates": ["messages"]
        }
        while 1:
            ans = self.post('getUpdates', data)
            if len(ans['result']) != 0:
                data['offset'] = ans['result'][0]['update_id'] + 1
                yield ans

    def listen(self):
        assert self.admin and self.TOKEN, 'No defined TOKEN and admin fields'
        if 'from reboot' in self._flags:
            self.report('View is restarted')
        else:
            self.report('View is launched')

        try:
            for update in self.__get_updates():
                update = update['result'][0]
                if 'message' in update:
                    message = update['message']
                    text = message['text']
                    sender = message['from']['id']
                    username = message['from']['username'] if 'username' in message['from'] else 'no username'
                    self.log(f"Came message: '{text}' from {sender} ({username})")
                    yield {
                        'message': text,
                        'sender': sender,
                        'username': username,
                        'platform': 'telegram'
                    }
                else:
                    self.log('UNHANDLED' + str(update))
        except:
            msg = format_exc()
            self.log(msg)
            self.report(msg)
