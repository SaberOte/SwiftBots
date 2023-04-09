from traceback import format_exc
import ast, threading, traceback
from . import crons


class Listener:
    def __init__(self, bot):
        self._bot = bot
        self.log = bot.log
        self.report = bot.report
        self.error = bot.error
        self.communicator = bot.communicator

    def check_handlers(self, command, view, context):
        plugins = self._bot.plugin_manager.plugins
        accepted_plugins = [x.lower() for x in view.plugins]
        plugins = list(filter(lambda plug: plug.__module__.split('.')[-1] in accepted_plugins, plugins))
        # check "cmds"
        for plugin in plugins:
            if command in plugin.cmds:
                return plugin.cmds[command], plugin
        # then check "prefixes"
        for plugin in plugins:
            for prefix in plugin.prefixes:
                if command.startswith(prefix):
                    if len(prefix) == len(command):
                        context['message'] = ''
                    elif command[len(prefix)] == ' ':
                        context['message'] = command[len(prefix)+1:]
                    else:
                        continue
                    return plugin.prefixes[prefix], plugin
        # finally check "any"
        for plugin in plugins:
            if callable(plugin.any):
                return plugin.any.__func__, plugin
        return None, None

    def handle_message(self, data, sender_view):
        context = ast.literal_eval(data)
        message = context['message']
        view = self._bot.views_manager.views[sender_view]
        method, plugin = self.check_handlers(message, view, context)
        if not plugin:
            view.unknown_command(context)
            return
        if not callable(method):
            self.error(
                f'There\'s fatal error! "{str(method)}" from class "{type(plugin).__name__}" is not a method '
                'or a function!')
            return
        self.log(f'Method "{method.__name__}" from class "{type(plugin).__name__}" is called')
        try:
            method(plugin, view, context)
        except Exception as e:
            view.error(format_exc(), context)

    def do_cron(self, plugin_name, task):
        raise Exception("Сейчас не работает. ИЗ за изменения контекста")
        plugin = None
        for plug in self._bot.plugin_manager.plugins:
            if task in plug.tasks:
                plugin = plug
        if not plugin:
            crons.remove(plugin_name, task)
            self.log(f'Message {task} is not recognized. Then removed')
            return
        task_info = plugin.tasks[task]
        view_name = task_info[2]
        try:
            view = next(filter(lambda x: x == view_name, self._bot.views_manager.views))
            view = self._bot.views_manager.views[view]
        except StopIteration:
            self.error(f'View {view_name} is disabled or does not exist. Call from cron {plugin_name} {task}')
            return
        method = task_info[0]
        if not callable(method):
            self.error(
                f'There\'s fatal error! "{str(method)}" from class "{type(plugin).__name__}" is not a method '
                'or a function!')
            return
        self.log(f'Method "{method.__name__}" from class "{type(plugin).__name__}" is called by cron')
        try:
            method(plugin, view)
        except Exception as e:
            self.error(
                f'Exception in "{method.__name__}" from "{type(plugin).__name__}":\n{str(type(e))}\n{str(e)}')

    def handle_signal(self, raw_data):
        try:
            # Могут прийти 3 типа сообщения:
            # mes|... - сообщение формата mes|информация. Приходит от вьюшки
            # cron|... - сообщение от крона. имеет формат plugin_name|task
            # report|... - сообщение от какого то компонента. Переслать одмену
            # Если ни один не подходит, то считается, что это сообщение от внутренних компонентов бота

            raw_message = raw_data['message']
            self.log(f'Came message: {raw_message}')
            if raw_message.startswith('mes|'):
                sender_view = raw_data['sender_view']
                self.handle_message(raw_message[4:], sender_view)
            elif raw_message.startswith('cron|'):
                plugin_name, task = raw_message[5:].split('|')
                if plugin_name is None or task is None:
                    self.error('Unknown form of cron task' + str(plugin_name) + ' ' + str(task))
                self.do_cron(plugin_name, task)
            elif raw_message.startswith('report|'):
                self.report(raw_message[7:])
            elif raw_message.startswith('started'):
                new_view = raw_data['sender_view']
                self._bot.views_manager.fill_views_dict([new_view])
            elif raw_message.startswith('unknown|'):
                self.report('View received unknown message: ' + raw_message[8:])
            else:
                self.report('Unknown message from ' + raw_data['sender_view'] + ' in listener:\n'+str(raw_message))

        except Exception as e:
            self.error(format_exc())
            # self.error(f'Exception in handling message:\n{str(type(e))}\n{str(e)}')

    def listen(self):
        self.log('Start listening...')
        while 1:
            try:
                for raw_data in self.communicator.listen():
                    threading.Thread(target=self.handle_signal, args=(raw_data,), daemon=True).start()
            except Exception as e:
                self.error(f'Exception in Listener:\n{str(type(e))}\n{str(e)}')
