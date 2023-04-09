import signal
import os
import time
from traceback import format_exc
from ...templates.telegram_view import TelegramView
from ...config import read_config


class AiTgView(TelegramView):
    plugins = ['gpt_ai']
    error_message = 'Произошла какая-то ошибка. Исправляем'

    def __init__(self):
        config = read_config('credentials.ini')
        self.TOKEN = config['AiTgView']['token']
        self.admin = config['AiTgView']['admin']

    def __handle_error(self, error):
        """overriden"""
        code = error['error_code']
        description = error['description']
        if code == 409:
            for i in range(2):
                self.report(str(i))
                time.sleep(1)
            os.kill(os.getpid(), signal.SIGKILL)
        if code == 400 and "can't parse" in description:  # Markdown не смог спарситься. Значит отправить в голом виде
            raise Exception('markdown is down')
        raise Exception(f"Error {code} from TG API: {description}")
