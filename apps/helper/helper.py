from requests.exceptions import ReadTimeout, ConnectionError
import time
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import threading
import subprocess
from sys import platform
from superapp import SuperApp, admin_only
class Helper(SuperApp):
    def __init__(self):
        super().__init__()

    @admin_only
    def launch_python(self, script, user):
        def func(args):
            if platform == 'linux': 
                subprocess.Popen(['python3']+args.split(' '))
            elif platform == 'win32':
                subprocess.Popen(['python']+args.split(' '))
            else: raise Exception('idiot?')
        if script == 'upbot':
            func('./../../upbot.py')
        
        else:
            func(script)

    @admin_only
    def doer(self, command, user):
        if command == 'status' or command == 'статус':
            self.sender.send(user, 'Helper активен!&#10004;')
            return

        if command == 'hi' or command == 'q':
            self.sender.send_sticker(user, 121) #4275
            return

        try:
            output = (subprocess.check_output(command.split(' '), timeout=10)).decode('utf-8')
        except subprocess.TimeoutExpired:
            self.sender.send(user, 'Зависло')
        except Exception as e:
            self.sender.send(user, f'Exception in helper:\n{str(type(e))}\n{str(e)}')

        if len(output) > 1:
            self.sender.send(user, output)
        else:
            self.sender.send(user, 'Вывода не будет')


    def launch(self):
        session = vk_api.VkApi(token=self.keys.public_token, api_version='5.103')
        lp = VkBotLongPoll(session, self.keys.public_id)
        while self.is_active:
            try:
                for event in lp.listen():
                    if self.is_active == False:
                        return
                    if event.type == VkBotEventType.MESSAGE_NEW:
                        msg = event.object.message.get('text')
                        if not msg.startswith(('do', 'Do')) and not msg.startswith(('python', 'Python')):
                            continue
                        user = str(event.object.message.get('from_id'))
                        self.log('There is message '+msg+' from user '+user)
                        if msg.startswith(('do', 'Do')):
                            command = msg[3:]
                            self.doer(command, user)
                        elif msg.startswith(('python', 'Python')):
                            command = msg[7:]
                            self.launch_python(command, user)

            except ReadTimeout:
                time.sleep(30)
            except ConnectionError:
                time.sleep(30)
            except Exception as e:
                self.sender.report("Exception in Helper!\n"+str(type(e))+'\n'+str(e))
                self.log(str(type(e))+'\n'+str(e))

    @admin_only
    def passer(self):
        pass

    prefixes = {
        "python" : passer,
        "do" : passer
            }
