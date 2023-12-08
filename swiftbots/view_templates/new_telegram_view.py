from swiftbots import BaseTelegramView


class ViewName(BaseTelegramView):
    controllers = []

    def __init__(self):
        self.init_credentials()
