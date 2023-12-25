"""Minimal demonstration of the simple chatbot view in the terminal"""
import asyncio
import os

from swiftbots.views import TelegramView


def input_async(*args, **kwargs):
    return asyncio.to_thread(input, *args, **kwargs)


class MyTgView(TelegramView):
    """
    Simple example how use telegram view
    """

    def __init__(self):
        token = os.environ.get('TELEGRAM_TOKEN')
        assert token, f'Missing environment variable "token"'
        admin = os.environ.get('TELEGRAM_ADMIN_ID')

        super().__init__(token, admin)
