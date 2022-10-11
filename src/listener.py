import cronmanager, ast, threading


class Listener:
    def __init__(self, bot):
        self._bot = bot
        self.log = bot.log
        self.report = bot.report
        self.error = bot.error
        self.communicator = bot.communicator

    def check_cmds(self, command, view):
        plugins = self._bot.plugins
        accepted_plugins = [x.lower() for x in view.plugins]
        plugins = filter(lambda plug: plug.__class__.__name__.lower() in accepted_plugins, plugins)
        for plugin in plugins:
            if command in plugin.cmds:
                return plugin.cmds[command], plugin
        return None, None

    def check_prefixes(self, command, view):
        plugins = self._bot.plugins
        accepted_plugins = [x.lower() for x in view.plugins]
        plugins = filter(lambda plug: plug.__class__.__name__.lower() in accepted_plugins, plugins)
        for plugin in plugins:
            for prefix in plugin.prefixes:
                if command.startswith(prefix):
                    if len(prefix) == len(command):
                        view.data['message'] = command
                    elif command[len(prefix)] == ' ':
                        view.data['message'] = command[len(prefix)+1:]
                    return plugin.prefixes[prefix], plugin
        return None, None

    def do_command(self, raw, sender):
        command = raw.split('|')[0]
        data = raw[1+len(command):]
        data = ast.literal_eval(data)
        view = self._bot.viewsManager.views[sender]
        view.data = data
        method, plugin = self.check_cmds(command, view)
        if not plugin:
            method, plugin = self.check_prefixes(command, view)
            if not plugin:
                view.unknown_command()
                return
        if not callable(method):
            self.error(
                f'There\'s fatal error! "{str(method)}" from class "{type(plugin).__name__}" is not a method '
                'or a function!')
            return
        self.log(f'Method "{method.__name__}" from class "{type(plugin).__name__}" is called')
        try:
            method(plugin, view)
        except Exception as e:
            self.error(
                f'Exception in "{method.__name__}" from "{type(plugin).__name__}":\n{str(type(e))}\n{str(e)}')
            view.error()

    def do_cron(self, plugin_name, task):
        plugin = None
        for plug in self._bot.plugins:
            if task in plug.tasks:
                plugin = plug
        if not plugin:
            cronmanager.remove(plugin_name, task)
            self.log(f'Message {task} is not recognized. Then removed')
            return
        task_info = plugin.tasks[task]
        view_name = task_info[2]
        try:
            view = next(filter(lambda x: x == view_name, self._bot.viewsManager.views))
            view = self._bot.viewsManager.views[view]
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

    def handle_message(self, raw_data):
        try:
            # могут прийти 3 типа сообщения:
            # com|... - сообщение формата com|команда|информация. Приходит от вьюшки
            # any|... - сообщение сразу с информацией. Не является командой, тупо пересылается плагину, ответственному
            #   за вьюшку, из которой сообщение прилетело
            # cron|... - сообщение от крона. имеет формат plugin_name|task
            # Если ни один не подходит, то считается, что это сообщение от внутренних компонентов бота (дебил????)
            print(raw_data)
            raw_message = raw_data['message']
            if raw_message.startswith('com|'):
                # надо вставить threading
                sender = raw_data['sender']
                self.do_command(raw_message[4:], sender)
            elif raw_message.startswith('cron|'):
                plugin_name, task = raw_message[5:].split('|')
                if plugin_name is None or task is None:
                    self.error('Unknown form of cron task' + str(plugin_name) + ' ' + str(task))
                self.do_cron(plugin_name, task)
            else:
                self.report('Unknown message from ' + raw_data['sender'] + ' in listener:\n'+str(raw_message))

        except Exception as e:
            self.error(f'Exception in Listener:\n{str(type(e))}\n{str(e)}')


    def listen(self):
        self.log('Start listening...')
        while 1:
            try:
                for raw_data in self.communicator.listen():
                    threading.Thread(target=self.handle_message, args=(raw_data,), daemon=True).start()
            except Exception as e:
                self.error(f'Exception in Listener:\n{str(type(e))}\n{str(e)}')
