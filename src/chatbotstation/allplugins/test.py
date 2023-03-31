from ..templates.super_plugin import SuperPlugin


class Test(SuperPlugin):
    def __init__(self, bot):
        super().__init__(bot)

    def tasktest(self, view):
        view.report('chat works')

    def pong(self, view):
        view.reply('pong 2')

    def lego(self, view):
        view.reply('poshel nahui')
        view.reply(view.context['message'])

    tasks = {
        # 'task_name' : (function_name, frequency_seconds)
        'kk': (tasktest, 5, 'tgview'),
        'free': (tasktest, 5, 'tgview')
    }
    prefixes = {
        # 'begin_of_command' : function_name
        'go': lego
    } # view.message - get message
    cmds = {
        'ping': pong
        # 'command' : function_name
    }
    any = None  # чтобы пихнуть в плагин любое неструктурированное всё что угодно. Конечно же должно быть функцией

