from traceback import format_exc
import requests
import json
from ..templates.super_plugin import SuperPlugin



class GPTAI(SuperPlugin):
    organization = "org-bsuVkr4uk7FuZ6v7B9xqidnk"
    api_key = ''
    url = 'https://api.openai.com/'
    model = "gpt-3.5-turbo"
    is_stream = False

    def __init__(self, bot):
        super().__init__(bot)
        # если нужно посчитать количество токенов,
        #   есть готовый код https://platform.openai.com/docs/guides/chat/introduction

    def post(self, parameters, body):
        headers = {
            'Authorization': 'Bearer ' + self.api_key,
            'OpenAI-Organization': self.organization
        }
        return requests.post(self.url+parameters, json=body, headers=headers)

    def handle(self, view, context):
        try:
            message = context['message']
            body = {
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": message}],
                "stream": self.is_stream
            }
            res = self.post('v1/chat/completions', body)
            if self.is_stream:
                whole_message = ''
                sender = context['sender']
                message_id = -1
                for line in res.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        assert line.startswith('data: '), 'corrupted json from openai. It is not "data: "'
                        if line == 'data: [DONE]':
                            view.update_message(message=whole_message, chat_id=sender, message_id=message_id)
                            return 'cool'
                        line = json.loads(line[6:])
                        line = line['choices'][0]['delta']
                        if 'content' in line and len(str(line['content'])) != 0:
                            whole_message += str(line['content'])
                        else:
                            continue
                    else:
                        continue
                    if message_id == -1:
                        resp = view.reply(whole_message+'....', context)
                        if not 'result' in resp:
                            raise Exception(str(resp))
                        message_id = resp['result']['message_id']
                    else:
                        view.update_message(message=whole_message+'....', chat_id=sender, message_id=message_id)
            else:
                try:
                    res = res.json()
                    res = res['choices'][0]['message']['content']
                except:
                    view.error(format_exc(), context)
                    view.report('Ответ непонятного формата: ' + str(res))
                    return
                view.reply(res, context)
        except:
            view.error(format_exc(), context)

    any = handle

