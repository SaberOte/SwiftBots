import os, time, datetime, requests, inspect, threading, superplugin, superview, sys, configparser, communicator
import subprocess

# from keys import KeyManager
# from msgsender import Sender
# from vkview import VkView
# from apimanager import ApiManager
from logger import Logger
from listener import Listener


class BotBase:
    plugins = []
    views = []

    def __init__(self, is_debug):
        self.__init_base_services(is_debug)
        self.__init_views()
        # self.__init_plugins()
        self.last_msg = time.time()

    def __init_base_services(self, is_debug):
        config = configparser.ConfigParser()
        config_path = '../resources/config.ini'
        config.read(config_path)
        if 'Disabled_Views' not in config.sections():
            config.add_section('Disabled_Views')
        if 'Names' not in config.sections():
            config.add_section('Names')
        if 'Tasks' not in config.sections():
            config.add_section('Tasks')
        with open(config_path, 'w') as file:
            config.write(file)
        logger = Logger(is_debug, './../logs/')
        self.log = logger.log
        self.log('Program is launching')
        # self.keys = KeyManager('./../resources/data.json', logger.log)
        # self.api = ApiManager(self.keys, logger.log)
        # self.sender = Sender('./../resources/', self.keys, self.api, logger.log)
        #self.__listener = Listener(self.log, self)
        # self.__vkview = VkView(self)
        # self.__monitoring_thread = threading.Thread(target=self.__listenVk__, daemon=True)
        self.start_time = datetime.datetime.utcnow()
        self.log('Base services are loaded')

    def __init_views(self):
        views_dir = [x for x in os.listdir('../views') if x.endswith('view')]
        imports = []
        for x in views_dir:
            try:
                imports.append(getattr(__import__(f'{x}.{x}'), x))
            except Exception as e:
                msg = f'Exception in the import view module({x}):\n{str(type(e))}\n{str(e)}'
                self.log(msg)
                ###### self.sender.report(msg)
        # print(imports[0].__name__.split('.')[0])
        # exit(1)
        views = []
        for x in imports:
            found = False
            for cls in inspect.getmembers(x, inspect.isclass):
                view_name = x.__name__.split('.')[0]
                if superview.SuperView in cls[1].__bases__ and cls[0].lower() == view_name:
                    views.append((view_name, cls[1]))  # составляется список вьюшек вида (название, класс)
                    found = True
                    break
            if not found:
                msg = 'Can\'t import view ' + x + '. This file does not contain class that inherited from SuperView and names like view folder'
                self.log(msg)
                ###### self.sender.report(msg)
        self.views = views
        self.log(f'Loaded views: {str(views)}')

        config = configparser.ConfigParser()
        config.read('../resources/config.ini')
        disabled_views = config.items('Disabled_Views')
        active_views = set(filter(lambda x: x[0].endswith('view'), config.items('Names')))
        comm = communicator.Communicator('../resources/config.ini', 'core_sender', self.log)
        running_views = filter(lambda view: comm.request('ping', view[0])['message'] == 'pong', active_views)
        comm.close()
        views_to_start = set(map(lambda x: x[0], views)) - set(map(lambda x: x[0], disabled_views)) - set(running_views)

        if len(views_to_start) > 0:
            old_path = os.getcwd()
            os.chdir('./../views/')
            for view in views_to_start:
                try:
                    subprocess.Popen(['python3', view, '{%s}' % view])
                except Exception as e:
                    os.chdir(old_path)
                    raise e
            os.chdir(old_path)
            self.log(str(views_to_start) + ' started')

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
        # self.__monitoring_thread.start()
        self.__listener.listen()

    def __listenVk__(self, mode=1):
        self.__vkview.listen()
