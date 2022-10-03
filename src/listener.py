import cronmanager, os


class Listener:
  def __init__(self, bot):
    self._bot = bot
    self.log = bot.log
    self.sender = bot.sender
    self.communicator = bot.communicator
  
  def listen(self):
    for command in self.communicator.listen():
      try:
        plugin_name, task = command['message'].split('|')

        plugin = None
        for plug in self._bot.plugins:
          if task in plug.tasks:
            plugin = plug
        if plugin == None:
          cronmanager.remove(plugin_name, task, os.path.split(os.getcwd())[0])
          self.log(f'Message {task} is not recognized. Then removed')
          continue
        method = plugin.tasks[task][0]
        if not callable(method):
            self.sender.report(f'There\'s fatal error! "{str(method)}" from class "{type(plugin).__name__}" is not a method or a function!')
            self.log(f'!!ERROR!!\nThere\'s fatal error! "{str(method)}" from class "{type(plugin).__name__}" is not a method or a function!')
            continue
        self.log(f'Method "{method.__name__}" from class "{type(plugin).__name__}" is called')
        try:
            method(plugin)
        except Exception as e:
            self.sender.report(f'Exception in "{method.__name__}" from "{type(plugin).__name__}":\n{str(type(e))}\n{str(e)}')
            self.log(f'!!ERROR!!\nException in "{method.__name__}" from "{type(plugin).__name__}":\n{str(type(e))}\n{str(e)}')
            continue
      except Exception as e:
        self.sender.report(f'Exception in Listener:\n{str(type(e))}\n{str(e)}')
        self.log(f'!!ERROR!!\nException in Listener:\n{str(type(e))}\n{str(e)}')
