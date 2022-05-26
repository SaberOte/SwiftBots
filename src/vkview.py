import time
from vk_api.bot_longpoll import VkBotEventType

class VkView:
    def __init__(self, bot):
        self._bot = bot
        self.keys = bot.keys
        self.log = bot.log
        self.plugins = bot.plugins
        self.lp = bot.api.lp
        self.sender = bot.sender
        self.api = bot.api
    
    def listen(self):
        self.log('Listening is started')
        for event in self.lp.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                message = event.object.message.get('text').lower()
                user_id = str(event.object.message.get('from_id'))

                self.log(f'\nThe message from "{user_id}" is catched: "{message}"')
                self._bot.last_msg = time.time()
                plugin = None
                #plugins
                for x in self.plugins:
                    if message in x.cmds:
                        plugin = x
                if plugin != None:
                    plugin.message = message
                    plugin.user_id = user_id
                    method = plugin.cmds.get(message)
                else:
                    #prefixes in plugins
                    for plug in self.plugins:
                        for pref in plug.prefixes:
                            if message.startswith(pref) and (message == pref or message[len(pref)] == ' '):
                                plugin = plug
                                if message == pref:
                                    plug.message = ''
                                else:
                                    plug.message = message[len(pref)+1:]
                                plugin.user_id = user_id
                                method = plugin.prefixes.get(pref)
                if plugin != None:
                    if not callable(method):
                        if user_id in self.keys.oper_ids and user_id != self.keys.admin_id:
                            self.sender.send(user_id, f'There\'s fatal error! "{str(method)}" from class "{type(plugin).__name__}" is not a method or a function!')
                        self.sender.report(f'There\'s fatal error! "{str(method)}" from class "{type(plugin).__name__}" is not a method or a function!')
                        self.log(f'!!ERROR!!\nThere\'s fatal error! "{str(method)}" from class "{type(plugin).__name__}" is not a method or a function!')
                        continue
                    self.log(f'Method "{method.__name__}" from class "{type(plugin).__name__}" is called')
                    try:
                        method(plugin)
                    except Exception as e:
                        if user_id in self.keys.oper_ids and user_id != self.keys.admin_id:
                            self.sender.send(user_id, f'Exception in "{method.__name__}" from "{type(plugin).__name__}":\n{str(type(e))}\n{str(e)}')
                        self.sender.report(f'Exception in "{method.__name__}" from "{type(plugin).__name__}":\n{str(type(e))}\n{str(e)}')
                        self.log(f'!!ERROR!!\nException in "{method.__name__}" from "{type(plugin).__name__}":\n{str(type(e))}\n{str(e)}')
                else:
                    self.unknown_cmd(user_id)

    def unknown_cmd(self, user_id):
        self.log('That\'s unknown command')
        if user_id == self.keys.admin_id:
            self.api.pub_api.messages.markAsRead(group_id=self.keys.public_id,mark_conversation_as_read=1,peer_id=user_id)
        else:
            self.sender.send(user_id, 'Неизвестная команда')
