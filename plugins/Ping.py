from superplugin import SuperPlugin, admin_only
#пример минимального приложения
class Ping(SuperPlugin):
    def __init__(self, bot):
        super().__init__(bot)

    def pong(self):
        self.sender.send(self.user_id, 'pong')

    cmds = {
        'ping' : pong
    }
