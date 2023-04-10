from vk_api.utils import get_random_id

def ExpCatcher(func):
    def do(self, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
        except Exception as e:
            try: 
                self.log(f'!!ERROR!! It\'s try to send error to admin about exception in Sender: \n' + 'Exception in Sender:\n'+str(type(e))+'\n'+str(e))
                self.api.messages.send(message=('Exception in Sender:\n' + str(type(e)) + '\n' + str(e)), user_id=)
            except Exception as ex:
                self.log('!!ERROR!! Sending is impossible. Critical error in Sender:\n'+str(type(ex))+'\n'+str(ex))
                import os, sys
                os._exit(1)
    return do

class Sender:
    def __init__(self, path, keys, api, log):
        self.keys = keys
        self.api = api.pub_api
        #self.keyboard=open(path+"keyboard.json", 'r', encoding="UTF-8").read()
        self.static_keyboard=open(path+"static_keyboard.json", 'r', encoding="UTF-8").read()        
        self.log = log

    @ExpCatcher
    def send(self, user_id, message):
        messages = []
        while len(message) > 4000:
            messages.append(message[:4000])
            message = message[4000:]
        messages.append(message)
        
        for msg in messages:
            if len(msg)==0:
                continue
            self.api.messages.send(message=msg, user_id=)
            self.log(f'The message is sent to "{user_id}": "{msg[:100] + "..." if len(msg) > 100 else msg}"')
        
    @ExpCatcher
    def send_sticker(self, user_id, sticker_id):
        self.api.messages.send(,
        self.log(f'The sticker "{sticker_id}" is sent to "{user_id}"')

    @ExpCatcher
    def send_menu(self, user_id):
        self.api.messages.send(message=open('./../resources/commands.txt', encoding="utf-8").read(), user_id=)
        self.log(f'The menu is sent to "{user_id}"')
    
    def error(self, user_id, msg):
        if user_id != self.keys.admin_id and user_id in self.keys.oper_ids:
            self.send(user_id,msg)
        self.report(msg)
    
    def report(self, message):
        self.send(self.keys.admin_id, message)
