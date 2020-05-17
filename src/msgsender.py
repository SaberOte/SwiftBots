from vk_api.utils import get_random_id

def ExpCatcher(func):
    def do(self, a, b):
        try:
            func(self, a, b)
        except Exception as e:
            try: 
                self.api.messages.send(
                            user_id=self.keys.admin_id,
                            random_id=get_random_id(),
                            message=('Exception in Sender:\n'+str(type(e))+'\n'+str(e))
                        )
            except Exception as ex:
                print('Critical error in Sender:\n'+str(type(ex))+'\n'+str(ex))
                import os, sys
                sys.stdout.flush()
                os._exit(1)
    return do

class Sender:
    def __init__(self, keys, api):
        self.keys = keys
        self.api = api.pub_api
        self.keyboard=open("./../resources/keyboard.json", 'r', encoding="UTF-8").read()
        self.static_keyboard=open("./../resources/static_keyboard.json", 'r', encoding="UTF-8").read()        

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
            self.api.messages.send(
                        user_id=user_id,
                        random_id=get_random_id(),
                        message=msg,
                        keyboard=self.static_keyboard
                    )
        
    #@ExpCatcher
    def send_sticker(self, user_id, sticker_id):
        self.api.messages.send(
                    user_id=user_id,
                    random_id=get_random_id(),
                    sticker_id=sticker_id,
                    keyboard=self.static_keyboard
                )

    #@ExpCatcher
    def send_menu(self):
        self.api.messages.send(
                    user_id=self.keys.admin_id,
                    random_id=get_random_id(),
                    message=open('./../resources/commands.txt', encoding="utf-8").read(),
                    keyboard=self.keyboard
                )
    
    def report(self, message):
        self.send(self.keys.admin_id, message)

    def debug(self, message):
        self.send(self.keys.debug_per_id, message)
