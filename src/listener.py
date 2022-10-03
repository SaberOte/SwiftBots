import cronmanager


class Listener:
    def __init__(self, bot):
        self._bot = bot
        self.log = bot.log
        self.report = bot.report
        self.communicator = bot.communicator

    def listen(self):
        self.log('Start listening...')
        for command in self.communicator.listen():
            print(command['message'])
            continue
            # пока что выключу
            try:
                plugin_name, task = command['message'].split('|')

                plugin = None
                for plug in self._bot.plugins:
                    if task in plug.tasks:
                        plugin = plug
                if not plugin:
                    cronmanager.remove(plugin_name, task)
                    self.log(f'Message {task} is not recognized. Then removed')
                    continue
                method = plugin.tasks[task][0]
                if not callable(method):
                    self.error(
                        f'There\'s fatal error! "{str(method)}" from class "{type(plugin).__name__}" is not a method ' 
                        'or a function!')
                    continue
                self.log(f'Method "{method.__name__}" from class "{type(plugin).__name__}" is called')
                try:
                    method(plugin)
                except Exception as e:
                    self.error(
                        f'Exception in "{method.__name__}" from "{type(plugin).__name__}":\n{str(type(e))}\n{str(e)}')
                    continue
            except Exception as e:
                self.error(f'Exception in Listener:\n{str(type(e))}\n{str(e)}')
