from src.botcore.templates.telegram_view import TelegramView
from src.botcore.config import read_config


class TestTgView(TelegramView):
    controllers = ['test']

    def __init__(self):
        config = read_config('credentials.ini')
        self.token = config['TestTgView']['token']
        self.admin = config['TestTgView']['admin']
