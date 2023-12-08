from swiftbots import BaseTelegramView


class TelegramView(BaseTelegramView):
    def __init__(self, oauth_token: str, admin_id: str = ''):
        self.token = oauth_token
        if admin_id:
            self.admin = admin_id
