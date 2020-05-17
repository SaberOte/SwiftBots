import time
import threading
import datetime
import requests
from keys import KeyManager
from doonline import Online
from msgsender import Sender
from listener import Listener
from apimanager import ApiManager
from controller import Controller

class BotBase:
    def __init__(self):
        self.keys = KeyManager()
        self.api = ApiManager(self.keys)
        self.sender = Sender(self.keys, self.api)
        self.online = Online(self.api.pub_api, self.sender.report, self.keys.public_id)
        self.ctrl = Controller(self)
        self.listener = Listener(self.ctrl, self.api.lp)
        self.start_time = datetime.datetime.utcnow()

    def start(self, mode=0):
        if mode == 0:
            pass #quiet start
        elif mode == 1:
            self.sender.send(self.keys.admin_id, 'Бот запущен!')
        elif mode == 2:
            self.sender.send(self.keys.admin_id, 'Бот перезапущен!')
        elif mode == 3:
            self.sender.send(self.keys.debug_person_id, 'Бот перезапущен!')
        

        self.listen()

    def listen(self):
        try:
            self.listener.listen()
        except requests.exceptions.ConnectionError:
            self.sender.send(self.keys.debug_person_id, 'Connection error in botbase')
            time.sleep(60)
            self.start(3)

        except requests.exceptions.ReadTimeout:
            self.sender.send(self.keys.debug_person_id, 'ReadTimeout (night reboot)')
            time.sleep(60)
            self.start(3)
        
        except Exception as e:
            self.sender.send(self.keys.admin_id, 'Exception in Listener:\n'+str(type(e))+'\n'+str(e))
            self.sender.send(self.keys.admin_id, 'Бот запустится через 60 секунд...')
            time.sleep(60)
            self.start(1)
