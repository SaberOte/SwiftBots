from vk_api.bot_longpoll import VkBotEventType

class Listener:
    def __init__(self, ctrl, lp):
        self.ctrl = ctrl
        self.lp = lp
    
    def listen(self):
        for event in self.lp.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                message = event.object.message.get('text').lower()
                self.ctrl.message = message
                self.ctrl.user_id = str(event.object.message.get('from_id'))

                if message.startswith('do'):
                    pass

                #white list commands for not admin

                if message == 'ping':
                    self.ctrl.send_pong()
                
                elif message in ('привет', 'доброе утро', 'hi', 'хай', 'хаюшки', 'приветики', 'ку', 'q', 'здравствуйте', 'здрасьте'):
                    self.ctrl.say_hi()

                #only admin commands after

                if self.ctrl.user_id != self.ctrl.keys.admin_id: 
                    self.ctrl.refuse()
                    
                if message == 'команды':
                    self.ctrl.send_menu()

                elif message in ('выход', 'exit', 'stop', 'остановить', 'выключить', 'turn off', 'turn down', 'вырубить', 'отключить', 'иди нахер', 'пошел в очко', 'отсоси', 'иди нахуй', 'умри', 'уйди'):
                    self.ctrl.exit()

                elif message == 'статус':
                    self.ctrl.common_status()

                elif message == 'запустить helper':
                    self.ctrl.start_helper()
                
                elif message in ('перезапустить', 'reboot', 'ребут', 'перезагрузить'):
                    self.ctrl.reboot()

                else:
                    self.ctrl.unknown_cmd()
