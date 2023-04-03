from traceback import format_exc
from ...templates.super_view import SuperView
import requests, os, time


class AITgView(SuperView):
    token = ''
    admin = '367363759'
    plugins = ['gptai']
    authentic_style = True
    error_message = 'Произошла какая-то ошибка. Исправляем'

    def post(self, method: str, data: dict):
        response = requests.get(f'https://api.telegram.org/bot{self.token}/{method}', json=data)
        answer = response.json()
        if not answer['ok']:
            self.__handle_error(answer)
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

    def custom_send(self, data):
        self.log(f'''Replied "{data['chat_id']}":\n"{data['text']}"''')
        return self.post('sendMessage', data)

    def __handle_error(self, error):
        code = error['error_code']
        description = error['description']
        if code == 409:
            for i in range(2):
                self.report(str(i))
                time.sleep(1)
            os._exit(1)
        if code == 400 and "can't parse" in description:  # markdown не смог спарситься. Значит отправить в голом виде
            raise Exception('markdown is down')
        self.report(f"Error {error['error_code']} from TG API: {error['description']}")
        raise Exception('Some error occured in ai tg view')

    def __skip_old_updates(self):
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

    def __get_updates(self):
        timeout = 1000
        offset = self.__skip_old_updates()
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

    def __hard_code(self, text):
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
            for update in self.__get_updates():
                update = update['result'][0]
                if 'message' in update:
                    message = update['message']
                    text = message['text']
                    sender = message['from']['id']
                    username = message['from']['username'] if 'username' in message['from'] else 'no username'
                    self.log(f"Came message: '{text}' from {sender} ({username})")
                    if self.__hard_code(text) == 22:
                        continue
                    yield {
                        'message': text,
                        'sender': sender
                    }
                else:
                    self.log('UNHANDLED' + str(update))
        except:
            msg = format_exc()
            self.log(msg)
            self.report(msg)
