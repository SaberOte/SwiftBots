"""Minimal demonstration of the simple telegram view"""
import os

from swiftbots.views import TelegramView


class MyTgView(TelegramView):
    """
    Simple example how use telegram view
    """

    def __init__(self):
        token = os.environ.get('TELEGRAM_TOKEN')
        assert token, f'Missing environment variable "TELEGRAM_TOKEN"'
        admin = os.environ.get('TELEGRAM_ADMIN_ID')

        super().__init__(token, admin)
