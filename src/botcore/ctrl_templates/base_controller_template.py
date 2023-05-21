# from src.botcore.bases.base_multiple_users_view import BaseMultipleUsersView
from src.botcore.bases.base_controller import BaseController, admin_only

class ControllerName(BaseController):
    def __init__(self, bot):
        super().__init__(bot)

    cmds = {}
    any = None
