import os, time, datetime, requests, inspect
from keys import KeyManager
from msgsender import Sender
from superplugin import SuperPlugin
from vkview import VkView
from apimanager import ApiManager
from logger import Logger

class BotBase:
    plugins = []
    def __init__(self, is_debug):
        self.__init_base_services(is_debug)
        self.__init_plugins()
        self.last_msg = time.time()
        self.__vkview = VkView(self)

    def __init_base_services(self, is_debug):
        logger = Logger(is_debug, './../logs/')
        self.log = logger.log
        self.log('Program is launching')
        self.keys = KeyManager('./../resources/data.json', logger.log)
        self.api = ApiManager(self.keys, logger.log)
        self.sender = Sender('./../resources/', self.keys, self.api, logger.log)
        self.start_time = datetime.datetime.utcnow()
        self.log('Base services are loaded')

    def __init_plugins(self):
        modules = [x[:-3] for x in os.listdir('./../plugins') if x.endswith('.py')]
        imports = []
        for x in modules:
            try:
                imports.append(__import__(x))
            except Exception as e:
                self.sender.report(f'Exception in the import module({x}):\n{str(type(e))}\n{str(e)}')
        self.log(f'Imported modules: {str(modules)}')
        all_classes = []
        for x in imports:
            for cls in inspect.getmembers(x, inspect.isclass):
                if SuperPlugin in cls[1].__bases__:
                    all_classes.append(cls[1])
        classes = []
        for x in all_classes:
            if x not in classes:
                classes.append(x)
        self.log(f'Loaded classes: {str(classes)}')
        for x in classes:
            self.plugins.append(x(self))
        self.log('Plugins are loaded')

    def _start_(self, mode=0):
        if mode == 0:
            pass #quiet start
        elif mode == 1:
            self.sender.report('Бот запущен!')
            self.log('Bot is started. mode %d' % mode) 
        elif mode == 2:
            self.sender.report('Бот перезапущен!')
            self.log('Bot is restarted %d' % mode) 
        elif mode == 3:
            self.log('Bot is restarted %d' % mode)
        
        self.__listen__()

    def __listen__(self):
        try:
            self.__vkview.listen()
        except requests.exceptions.ConnectionError:
            self.log('Connection ERROR in botbase')
            time.sleep(60)
            self._start_(3)

        except requests.exceptions.ReadTimeout:
            self.log('ReadTimeout (night reboot)')
            time.sleep(60)
            self._start_(3) 
        
        except Exception as e:
            self.sender.report('Exception in Botbase:\n'+str(type(e))+'\n'+str(e))
            self.sender.report('Бот запустится через 5 секунд')
            self.log('!!ERROR!!\nException in Botbase:\n'+str(type(e))+'\n'+str(e))
            time.sleep(5)
            self._start_(2)
