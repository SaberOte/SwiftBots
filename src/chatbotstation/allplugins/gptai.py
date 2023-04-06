from traceback import format_exc
import requests
import json
from ..config import read_config
from ..templates.super_plugin import SuperPlugin
from ..allviews.ai_tg_view.ai_tg_view import AiTgView


def escape_markdown_chars(string: str) -> str:
    """Escape characters '_', '*', '['. Bot don't escape these in code. Code is block with '`' characters by sides"""
    """
        Внутри блока кода, обособленного '```' ничего не должно быть экранировано
        Внутри встроенного кода, обособленного '`' ничего не должно быть экранировано
        Экранировать символы '_', '*', '['

        Если нет закрывающего '```', то он должен быть добавлен в конец
        Если нет закрывающего '`', то он должен быть добавлен в конец
        Если активно состояние встроенного кода, то может быть открыто состояние блока кода. Наоборот - нет!
    """
    code_block = False
    escaped_string = ''
    for i in range(len(string)):
        if string[i] == '`':
            code_block = not code_block
            escaped_string += '`'
        elif code_block:
            escaped_string += string[i]
        elif string[i] in ['_', '*', '[']:
            escaped_string += '\\' + string[i]
        else:
            escaped_string += string[i]
    if code_block:
        # if it's odd number of '`' chars, code will be ruined, so add to the end
        escaped_string += '`'
    return escaped_string


def receive_non_stream(response, view: AiTgView, context: dict):
    try:
        message = response.json()
        message = message['choices'][0]['message']['content']
    except:
        view.error(format_exc(), context)
        view.report('Ответ непонятного формата: ' + str(response))
        return
    data = {
        "chat_id": context['sender'],
        "text": escape_markdown_chars(message),
        "parse_mode": 'Markdown'
    }
    try:
        view.custom_send(data)
    except Exception as e:
        if str(e) == 'markdown is down':
            view.reply(message, context)
        else:
            raise e


def update_stream(message, message_id, view, context):
    data = {
        "chat_id": context['sender'],
        "text": escape_markdown_chars(message),
        "message_id": message_id,
        "parse_mode": 'Markdown'
    }
    try:
        view.update_message(data)
    except Exception as e:
        if str(e) == 'markdown is down':
            data = {
                "chat_id": context['sender'],
                "text": message,
                "message_id": message_id,
            }
            view.update_message(data)
        else:
            raise e


def receive_stream(response, view: AiTgView, context: dict):
    whole_message = ''
    message_id = -1
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            assert line.startswith('data: '), 'corrupted json from openai. It is not "data: "'
            if line == 'data: [DONE]':
                update_stream(whole_message, message_id, view, context)
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
            resp = view.reply(whole_message + '....', context)
            message_id = resp['result']['message_id']
        else:
            update_stream(whole_message+'....', message_id, view, context)


class GptAi(SuperPlugin):
    OPENAI_URL = 'https://api.openai.com/'
    GPT_MODEL = "gpt-3.5-turbo"
    is_stream = True

    def __init__(self, bot):
        super().__init__(bot)
        config = read_config('credentials.ini')
        self.ORGANIZATION = config['OpenAI']['organization']
        self.API_KEY = config['OpenAI']['api_key']
        # если нужно посчитать количество токенов,
        #   есть готовый код https://platform.openai.com/docs/guides/chat/introduction

    def post(self, parameters, body):
        headers = {
            'Authorization': 'Bearer ' + self.API_KEY,
            'OpenAI-Organization': self.ORGANIZATION
        }
        return requests.post(self.OPENAI_URL + parameters, json=body, headers=headers)

    def handle(self, view: AiTgView, context):
        message = context['message']
        body = {
            "model": self.GPT_MODEL,
            "messages": [{
                "role": "user",
                "content": message}],
            "stream": self.is_stream
        }
        res = self.post('v1/chat/completions', body)
        if self.is_stream:
            receive_stream(res, view, context)
        else:
            receive_non_stream(res, view, context)

    def disable_stream(self, view: AiTgView, context):
        self.is_stream = False
        view.reply('stream disabled', context)

    def enable_stream(self, view: AiTgView, context):
        self.is_stream = True
        view.reply('stream enabled!', context)

    cmds = {
        "stream disable": disable_stream,
        "stream enable": enable_stream
    }

    any = handle
