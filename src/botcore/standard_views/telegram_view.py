import os
from src.botcore.bases.base_telegram_view import BaseTelegramView


class TelegramView(BaseTelegramView):
    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.admin = os.getenv('ADMIN_ID')
