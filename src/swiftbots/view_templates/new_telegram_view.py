from src.swiftbots.bases.base_telegram_view import BaseTelegramView


class ViewName(BaseTelegramView):
    controllers = []

    def __init__(self):
        self.init_credentials()
