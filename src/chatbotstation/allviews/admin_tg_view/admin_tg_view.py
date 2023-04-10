from ...templates.telegram_view import TelegramView
from ...config import read_config


class AdminTgView(TelegramView):
    plugins = ['admin_panel']

    def __init__(self):
        config = read_config('credentials.ini')
        self.token = config['AdminTgView']['token']
        self.admin = config['AdminTgView']['admin']
