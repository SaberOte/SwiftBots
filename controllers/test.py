from src.chatbotstation.templates.super_controller import SuperController
from src.chatbotstation.templates.super_view import SuperView


class Test(SuperController):
    def __init__(self, bot):
        super().__init__(bot)

    def tasktest(self, view: SuperView, context):
        view.report('chat works')

    def pong(self, view: SuperView, context):
        view.reply('pong 2', context)

    def lego(self, view: SuperView, context):
        view.reply('poshel nahui', context)
        view.reply(context['message'], context)

    def do(self, view: SuperView, context):
        msg = context['message']
        view.reply(str(len(msg)), context)

    tasks = {
        # 'task_name' : (function_name, frequency_seconds)
        'kk': (tasktest, 5, 'tgview'),
        'free': (tasktest, 5, 'tgview')
    }
    prefixes = {
        'go': lego
    }
    cmds = {
        'ping': pong
    }
    any = do
