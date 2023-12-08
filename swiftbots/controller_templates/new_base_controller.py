# from src.swiftbots.bases.base_multiple_users_view import BaseChatView
from swiftbots import BaseController


class ControllerName(BaseController):
    def __init__(self, bot):
        super().__init__(bot)

    cmds = {}
    any = None
