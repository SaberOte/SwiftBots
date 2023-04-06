import requests
import os
from traceback import format_exc
from ...templates.super_view import SuperView
from ...config import read_config


class TgView(SuperView):
    plugins = ['adminpanel']
    authentic_style = True

    def __init__(self):
        config = read_config('credentials.ini')
        self.TOKEN = config['TgView']['token']
        self.admin = config['TgView']['admin']

    def get(self, method, data=''):
        answer = requests.get(f'https://api.telegram.org/bot{self.TOKEN}/{method}?{data}')
        return answer.json()

    def skip_old_updates(self):
        ans = self.get('getUpdates', f'timeout=0&limit=1&offset=-1')
        result = ans['result']
        if len(result) > 0:
            return result[0]['update_id']+1
        return -1

    def get_updates(self):
        timeout = 1000
        offset = self.skip_old_updates()
        while 1:
            ans = self.get('getUpdates', f'timeout={timeout}&limit=1&offset={offset}&allowed_updates=["message"]')
            if not ans['ok']:
                if ans['error_code'] == 409:
                    os._exit(1)
                raise Exception(str(ans['error_code']) + ' ' + ans['description'])
            if len(ans['result']) != 0:
                offset = ans['result'][0]['update_id']+1
                yield ans

    def hard_code(self, text):
        if text == 'selfexit':
            self.report('exited')
            self.comm.close()
            self.log('exited')
            os._exit(1)
        if text == 'hey':
            self.report('Hola der Fruend!')
            return 22

    def listen(self):
        self.report('TGView запущен')
        try:
            for update in self.get_updates():
                update = update['result'][0]
                if 'message' in update:
                    message = update['message']
                    text = message['text']
                    sender = message['from']['id']
                    self.log(f"Came message: '{text}' from {sender} ({message['from']['username']})")
                    if self.hard_code(text) == 22:
                        continue
                    yield {
                        'message': text,
                        'sender': sender,
                    }
                else:
                    self.log('UNHANDLED' + str(update))
        except:
            self.log(format_exc())

    def send(self, message, chat_id):
        return self.get('sendMessage', f'chat_id={chat_id}&text={message}')
