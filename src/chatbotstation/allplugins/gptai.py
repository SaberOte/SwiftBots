from traceback import format_exc
import requests
from ..templates.super_plugin import SuperPlugin


class GPTAI(SuperPlugin):
    organization = "org-bsuVkr4uk7FuZ6v7B9xqidnk"
    api_key = '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'
    url = 'https://api.openai.com/'
    model = "gpt-3.5-turbo"
    is_stream = True

    def __init__(self, bot):
        super().__init__(bot)
        # если нужно посчитать количество токенов,
        #   есть готовый код https://platform.openai.com/docs/guides/chat/introduction

    def get(self, parameters, body):
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
            res = self.get('v1/chat/completions', body)
            if self.is_stream:
                whole_message = b''
                for line in res.iter_lines():
                    if line:
                        whole_message += line
                view.reply(str(whole_message))
            else:
                try:
                    res = res.json()
                    res = res['choices'][0]['message']['content']
                except:
                    view.reply('Ошибка! Скоро будет исправлена')
                    view.report(format_exc())
                    view.report('Ответ непонятного формата: ' + str(res))
                    return
                view.reply(res)
        except:
            view.report(format_exc())

    any = handle

