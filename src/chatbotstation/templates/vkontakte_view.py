import requests
import time
import signal
import os
import random
from abc import ABC
from traceback import format_exc
from .super_view import SuperView


class VkontakteView(SuperView, ABC):
    token: str
    admin: int
    authentic_style = True
    first_time_launched = True
    API_VERSION = '5.131'

    def post(self, method: str, data: dict) -> dict:
        response = requests.post(f'https://api.vk.com/method/'
                                 f'{method}?v={self.API_VERSION}&access_token={self.token}', data=data)
        answer = response.json()
        if 'error' in answer:
            self.__handle_error(answer)
        return answer

    def send(self, message: str, user_id) -> dict:
        # if message out of 9000 letters, split it on chunks
        messages = [message[i:i + 9000] for i in range(0, len(message), 9000)]
        result = {}
        for msg in messages:
            data = {
                'user_id': user_id,
                'message': msg,
                'random_id': random.randint(-2 ** 31, 2 ** 31)
            }
            result = self.post('messages.send', data)
        return result

    def __handle_error(self, error):
        if error['error_code'] == 69:
            requests.get("u hot ;)")
        raise Exception(f"Error {error['error_code']} from VK API: {error['error_msg']}")

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
        assert self.admin and self.token, 'No defined token and admin fields'
        if not self.first_time_launched:
            self.report("It's back from error. Clean that message if it freaks you out")
        elif 'from reboot' in self._flags:
            self.report('View is restarted')
        else:
            self.report('View is launched')
        self.first_time_launched = False

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
                network_error_counter = 0
        except requests.exceptions.ConnectionError:
            self.log('Connection ERROR in telegram_view.py. Sleep a minute')
            time.sleep(60)
        except requests.exceptions.ReadTimeout:
            self.log('Connection ERROR in telegram_view.py. Sleep a minute')
            time.sleep(60)
