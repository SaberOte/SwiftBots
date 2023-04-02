from traceback import format_exc
from ...templates.super_view import SuperView
import requests, os, sys, time


class AITgView(SuperView):
    token = '5724561112:AAG6S6XjSOwwyKntffU64lEoYR1c780N3WI'
    admin = '367363759'
    plugins = ['gptai']
    authentic_style = True
    error_message = 'Произошла какая-то ошибка. Исправляем'

    def post(self, method: str, data: dict):
        response = requests.get(f'https://api.telegram.org/bot{self.token}/{method}', json=data)
        answer = response.json()
        if not answer['ok']:
            self.handle_error(answer)
        return answer

    def update_message(self, message, chat_id, message_id):
        data = {
            "chat_id": chat_id,
            "text": message,
            "message_id": message_id
        }
        return self.post('editMessageText', data)

    def send(self, message, chat_id):
        data = {
            "chat_id": chat_id,
            "text": message
        }
        return self.post('sendMessage', data)

    def handle_error(self, error):
        code = error['error_code']
        if code == 409:
            for i in range(2):
                self.report(str(i))
                time.sleep(1)
            os._exit(1)
        self.report(f"Error {error['error_code']} from TG API: {error['description']}")
        raise Exception('Some error occured in ai tg view')

    def skip_old_updates(self):
        data = {
            "timeout": 0,
            "limit": 1,
            "offset": -1
        }
        ans = self.post('getUpdates', data)
        result = ans['result']
        if len(result) > 0:
            return result[0]['update_id']+1
        return -1

    def get_updates(self):
        timeout = 1000
        offset = self.skip_old_updates()
        data={
            "timeout": timeout,
            "limit": 1,
            "offset": offset,
            "allowed_updates": ["messages"]
        }
        while 1:
            ans = self.post('getUpdates', data)
            if len(ans['result']) != 0:
                data['offset'] = ans['result'][0]['update_id']+1
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
        self.report('AI Tg View запущен')
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
                        'sender': sender
                    }
                else:
                    self.log('UNHANDLED' + str(update))
        except:
            self.log(format_exc())
