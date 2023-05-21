import requests
import time
import signal
import os
from abc import ABC
from traceback import format_exc
from src.botcore.bases.base_multiple_users_view import BaseMultipleUsersView


class BaseTelegramView(BaseMultipleUsersView, ABC):
    token: str
    admin: str
    first_time_launched = True
    skip_old_updates = False

    def post(self, method: str, data: dict) -> dict:
        response = requests.post(f'https://api.telegram.org/bot{self.token}/{method}', json=data)
        answer = response.json()
        if not answer['ok']:
            self._handle_error(answer)
        return answer

    def init_credentials(self):
        self.token = os.environ['TELEGRAM_TOKEN']
        self.admin = os.environ['ADMIN_ID']

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
        Standard send provides only message and chat_id arguments.
        This method can contain any fields in data
        :param data:
        """
        self.log(f"""Replied {data["chat_id"]}:\n'{data["text"]}'""")
        return self.post('sendMessage', data)

    def delete_message(self, message_id, chat_id):
        data = {
            "chat_id": chat_id,
            "message_id": message_id
        }
        return self.post('deleteMessage', data)

    def _handle_error(self, error):
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

    def _get_updates(self):
        timeout = 1000
        data = {
            "timeout": timeout,
            "limit": 1,
            "allowed_updates": ["messages"]
        }
        if self.first_time_launched or self.skip_old_updates:
            self.first_time_launched = False
            data['offset'] = self.__skip_old_updates()
        while 1:
            ans = self.post('getUpdates', data)
            if len(ans['result']) != 0:
                data['offset'] = ans['result'][0]['update_id'] + 1
                yield ans

    def listen(self):
        """
        Input pipe for commands from user.
        Method must use "yield" operator to give information and command
        Example: yield {'sender': user_id, 'message': command}
        `sender` is required property
        """
        assert self.admin and self.token, 'No defined token and admin fields'
        if 'from reboot' in self._flags:
            self.report('View is restarted')
        else:
            self.report('View is launched')

        try:
            for update in self._get_updates():
                try:
                    update = update['result'][0]
                    if 'message' in update and 'text' in update['message']:
                        message = update['message']
                        text = message['text']
                        sender = message['from']['id']
                        username = message['from']['username'] if 'username' in message['from'] else 'no username'
                        self.log(f"Came message from {sender} ({username}): '{text}'")
                        yield {
                            'message': text,
                            'sender': sender,
                            'username': username,
                            'platform': 'telegram'
                        }
                    else:
                        self.log('UNHANDLED\n', str(update))
                except Exception as e:
                    msg = 'Unhandled:' + '\nAnswer is:\n' + str(update) + '\n' + format_exc() 
                    try:
                        self.error(msg, update['message']['from']['id'])
                    except:
                        self.try_report(msg)
                        self.try_report('error number 0x8923')
        except requests.exceptions.ConnectionError as e:
            self.log('Connection ERROR in base_telegram_view.py. Sleep a minute')
            reported = 1 # = self.try_report('connection error')
            if reported != 1:
                self.log('Not reported', reported)
            time.sleep(5)
        except requests.exceptions.ReadTimeout as e:
            self.log('Connection ERROR in base_telegram_view.py. Sleep a minute', e)
            reported = 1 # = self.try_report('read timeout error')
            if reported != 1:
                self.log('Not reported', reported)
            time.sleep(5)
