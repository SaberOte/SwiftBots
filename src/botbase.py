import os, time, datetime, requests, inspect, threading, superplugin, superview, sys, configparser
#from keys import KeyManager
#from msgsender import Sender
#from vkview import VkView
#from apimanager import ApiManager
from logger import Logger
from listener import Listener

class BotBase:
    plugins = []
    views = []
    view_threads = []
    def __init__(self, is_debug):
        self.__init_base_services(is_debug)
        self.__init_views()
        #self.__init_plugins()
        self.last_msg = time.time()

    def __init_base_services(self, is_debug):
        logger = Logger(is_debug, './../logs/')
        self.log = logger.log
        self.log('Program is launching')
        #self.keys = KeyManager('./../resources/data.json', logger.log)
        #self.api = ApiManager(self.keys, logger.log)
        #self.sender = Sender('./../resources/', self.keys, self.api, logger.log)
        self.__listener = Listener(self.log, self)
        #self.__vkview = VkView(self)
        #self.__monitoring_thread = threading.Thread(target=self.__listenVk__, daemon=True)
        self.start_time = datetime.datetime.utcnow()
        self.log('Base services are loaded')

    def __init_views(self):
#
        self.log = print
#
        views_dir = [x for x in os.listdir('../views') if x.endswith('view')]
        imports = []
        for x in views_dir:
            try:
                imports.append(getattr(__import__(f'{x}.{x}'), x))
            except Exception as e:
                print(e)
                #vk#self.sender.report(f'Exception in the import view module({x}):\n{str(type(e))}\n{str(e)}')
        views = []
        for x in imports:
            for cls in inspect.getmembers(x, inspect.isclass):
                if superview.SuperView in cls[1].__bases__:
                    views.append(cls[1])
                else:
                    pass
                    #self.sender.report('Can\'t import class ' + cls + ' that not inherited from SuperView')
        for x in views:
            self.views.append(x(self))
        self.log(f'Loaded views: {str(views)}')

    def __init_plugins(self):
        modules = [x[:-3] for x in os.listdir('./../plugins') if x.endswith('.py')]
        imports = []
        for x in modules:
            try:
                imports.append(__import__(x))
            except Exception as e:
                self.sender.report(f'Exception in the import module({x}):\n{str(type(e))}\n{str(e)}')
        all_classes = []
        for x in imports:
            for cls in inspect.getmembers(x, inspect.isclass):
                if superplugin.SuperPlugin in cls[1].__bases__:
                    all_classes.append(cls[1])
        classes = []
        for x in all_classes:
            if x not in classes:
                classes.append(x)
        for x in classes:
            self.plugins.append(x(self))
        self.log(f'Loaded classes: {str(classes)}')

    def _start_(self):
        #self.__monitoring_thread.start()
        self.__listener.listen()

    def __listenVk__(self, mode=1):
      self.__vkview.listen()
