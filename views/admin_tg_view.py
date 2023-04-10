from src.botcore.templates.telegram_view import TelegramView
from src.botcore.config import read_config


class AdminTgView(TelegramView):
    controllers = ['admin_panel']

    def __init__(self):
        config = read_config('credentials.ini')
        self.token = config['AdminTgView']['token']
        self.admin = config['AdminTgView']['admin']
