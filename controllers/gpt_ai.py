from traceback import format_exc
import requests
import json
import base64
import threading
import time
import psycopg2
from ..config import read_config
from ..templates.super_controller import SuperController, admin_only
from ..allviews.ai_tg_view import AiTgView


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


def handle_openai_error(response, view: AiTgView, context):
    error = response['error']
    if error['code'] == 'context_length_exceeded':
        # delete current context
        deactivate_gpt_context(context)
        view.report(f'Контекст перегрузился у {context["username"]}. Удалён')
        if str(context['sender']) != str(view.admin):
            view.reply('Контекст перегружен. Если сообщение слишком большое, попробуйте спрашивать по частям', context)
        return
    view.error(str(error), context)


def receive_non_stream(response, view: AiTgView, context: dict) -> str:
    try:
        message = response.json()
        if 'error' in message:
            handle_openai_error(message, view, context)
            return ''
        message = message['choices'][0]['message']['content']
    except Exception:
        view.error(format_exc(), context)
        raise Exception('Ответ непонятного формата: ' + str(response.json()))
    data = {
        "chat_id": context['sender'],
        "text": escape_markdown_chars(message),
        "parse_mode": 'Markdown'
    }
    try:
        view.custom_send(data)
        return message
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


def iter_stream(response, stream: dict):
    try:
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                assert line.startswith('data: '), 'corrupted json from openai. It is not "data: "'
                if line == 'data: [DONE]':
                    stream['done'] = True
                    return
                line = json.loads(line[6:])
                line = line['choices'][0]['delta']
                if 'content' in line and len(str(line['content'])) != 0:
                    stream['content'] += str(line['content'])
                else:
                    continue
            else:
                continue
    except Exception as e:
        stream['error_message'] = str(e)
    finally:
        stream['done'] = True


def receive_stream(response, view: AiTgView, context: dict) -> str:
    message_id = -1
    delay = 0.01
    stream = {"content": "", "done": False}  # packing in dict.
    # It's an only way to not copy object when transfer via functions
    threading.Thread(target=iter_stream, daemon=True, args=(response, stream)).start()
    copy_message = ''
    while 1:
        done = stream['done']
        content = stream['content']
        if done and 'error_message' in stream:
            view.error(stream['error_message'], context)
            return ''
        elif done:
            if message_id == -1:
                view.reply(content, context)
            else:
                update_stream(content, message_id, view, context)
            return content
        elif content == copy_message:
            pass
        elif message_id == -1:
            resp = view.reply(content + '....', context)
            message_id = resp['result']['message_id']
        else:
            update_stream(content+'....', message_id, view, context)
        copy_message = content
        time.sleep(delay)
        view.reply('wait', context)


def receive_stream_obsolete(response, view: AiTgView, context: dict) -> str:
    whole_message = ''
    message_id = -1
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            assert line.startswith('data: '), 'corrupted json from openai. It is not "data: "'
            if line == 'data: [DONE]':
                update_stream(whole_message, message_id, view, context)
                return whole_message
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


def db_execute(cred: list, sql: str, is_commit=False):
    conn = psycopg2.connect(f"dbname={cred[0]} user={cred[1]} password={cred[2]}")
    result = None
    try:
        cur = conn.cursor()
        cur.execute(sql)
        if is_commit:
            conn.commit()
        else:
            result = cur.fetchall()
        cur.close()
    finally:
        conn.close()
    return result


def deactivate_gpt_context(context):
    user = load_user(context)
    gpt_context_id = load_gpt_context(context, user)
    sql = f"""UPDATE gpt_context 
            SET is_deactivated=true,
            is_current=false
            WHERE id={gpt_context_id}"""
    db_execute(context['db_credentials'], sql, is_commit=True)


def load_user(context) -> int:
    """
    Registers if there is no such user
    :return: user id, int
    """
    db_cred = context['db_credentials']
    for _ in range(2):
        sql = f"""SELECT id
        FROM gpt_user
        WHERE platform_id='{context['sender']}'
        AND platform_at='{context['platform']}'"""
        user_id = db_execute(db_cred, sql)

        if len(user_id) == 0:
            # register
            sql = f"""INSERT INTO gpt_user (platform_id, platform_at, name)
            VALUES ('{context["sender"]}', '{context["platform"]}', '{context["username"]}')"""
            db_execute(db_cred, sql, True)
            continue  # try to receive id one more time

        return user_id[0][0]


def save_context(context, gpt_context_id, completion):
    db_cred = context['db_credentials']
    msg1 = context["message"]
    msg2 = completion
    msg1 = base64.b64encode(msg1.encode('utf-8')).decode('utf-8')
    msg2 = base64.b64encode(msg2.encode('utf-8')).decode('utf-8')
    msg1 = msg1.replace("'", "<SINGLE_QUOTE>")
    msg2 = msg2.replace("'", "<SINGLE_QUOTE>")
    # user message at first
    sql = f"""INSERT INTO gpt_message (message, role, context)
                VALUES ('{msg1}', 'user', '{gpt_context_id}')"""
    db_execute(db_cred, sql, True)
    # then assistant message
    sql = f"""INSERT INTO gpt_message (message, role, context)
                VALUES ('{msg2}', 'assistant', '{gpt_context_id}')"""
    db_execute(db_cred, sql, True)


def load_gpt_context(context, user_id: int) -> (list, int):
    """
    Creates context if there is no active for this user
    :return: context_id, int
    """
    db_cred = context['db_credentials']
    for _ in range(2):
        sql = f"""SELECT id
        FROM gpt_context
        WHERE user_id={user_id}
        AND is_current=true
        AND is_deactivated=false"""
        gpt_context_id = db_execute(db_cred, sql)

        if len(gpt_context_id) == 0:
            # create
            sql = f"""INSERT INTO gpt_context (user_id)
            VALUES ('{user_id}')"""
            db_execute(db_cred, sql, True)
            continue  # try to receive id one more time

        return gpt_context_id[0][0]


def load_gpt_messages(context, gpt_context_id: int) -> list:
    """
    :return: list[{'role': 'user', 'content': 'hello'},
                  {'role': 'assistant', 'content': 'Hello! I'm freaking assistant!'}]
    """
    db_cred = context['db_credentials']
    sql = f"""SELECT role, message
                    FROM gpt_message
                    WHERE context={gpt_context_id}
                    ORDER BY id"""
    messages = db_execute(db_cred, sql)

    def decode(msg):
        msg = msg.replace('<SINGLE_QUOTE>', "'")
        msg = base64.b64decode(msg.encode('utf-8')).decode('utf-8')
        return msg
    messages = [{'role': row[0], 'content': decode(row[1])} for row in messages]
    return messages


class GptAi(SuperController):
    OPENAI_URL = 'https://api.openai.com/'
    GPT_MODEL = "gpt-3.5-turbo"
    is_stream = False

    def __init__(self, bot):
        super().__init__(bot)
        config = read_config('credentials.ini')
        self.ORGANIZATION = config['OpenAI']['organization']
        self.API_KEY = config['OpenAI']['api_key']
        self.db_password = config['Database']['password']
        self.db_login = config['Database']['login']
        self.db_name = config['Database']['db']
        # если нужно посчитать количество токенов,
        #   есть готовый код https://platform.openai.com/docs/guides/chat/introduction

    def post(self, parameters, body):
        headers = {
            'Authorization': 'Bearer ' + self.API_KEY,
            'OpenAI-Organization': self.ORGANIZATION
        }
        return requests.post(self.OPENAI_URL + parameters, json=body, headers=headers)

    def handle(self, view: AiTgView, context):
        context['db_credentials'] = self.get_cred()
        user_id = load_user(context)
        gpt_context_id = load_gpt_context(context, user_id)
        context_messages = load_gpt_messages(context, gpt_context_id)
        message = context['message']
        context_messages.append({'role': 'user', 'content': message})
        context_messages = context_messages[-8:]
        body = {
            "model": self.GPT_MODEL,
            "messages": context_messages,
            "stream": self.is_stream
        }
        res = self.post('v1/chat/completions', body)
        if self.is_stream:
            completion = receive_stream(res, view, context)
        else:
            completion = receive_non_stream(res, view, context)
        if completion:
            save_context(context, gpt_context_id, completion)

    @admin_only
    def disable_stream(self, view: AiTgView, context):
        self.is_stream = False
        view.reply('stream disabled', context)

    @admin_only
    def enable_stream(self, view: AiTgView, context):
        self.is_stream = True
        view.reply('stream enabled!', context)

    def get_cred(self):
        return [self.db_name, self.db_login, self.db_password]

    cmds = {
        "stream off": disable_stream,
        "off stream": disable_stream,
        "stream on": enable_stream,
        "on stream": enable_stream
    }

    any = handle
