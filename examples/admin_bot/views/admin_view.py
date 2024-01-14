import os

from swiftbots.views import TelegramView


class AdminView(TelegramView):
    """
    Simple example how use telegram view
    """

    def __init__(self):
        token = os.environ.get('TEST_TG_TOKEN')
        assert token, 'Missing environment variable "TELEGRAM_TOKEN"'
        admin = os.environ.get('TG_ADMIN')

        super().__init__(token, admin)
