import os, time, datetime, inspect, threading, superplugin, superview, configparser, communicator
from viewsmanager import ViewsManager
from logger import Logger
from listener import Listener


class BotBase:
    plugins = []

    def __init__(self, is_debug):
        self.start_time = datetime.datetime.utcnow()
        self.__init_base_services(is_debug)
        self.__init_views()
        self.sender = self.viewsManager.get_sender()
        # self.__init_plugins()
        self.last_msg = time.time()
        self.__listener = Listener(self)

    def __fill_config(self):
        config = configparser.ConfigParser()
        config_path = '../resources/config.ini'
        config.read(config_path)
        if 'Disabled_Views' not in config.sections():
            config.add_section('Disabled_Views')
        if 'Names' not in config.sections():
            config.add_section('Names')
        if 'Tasks' not in config.sections():
            config.add_section('Tasks')
        if 'Main_View' not in config.sections():
            config.add_section('Last_Views')
        with open(config_path, 'w') as file:
            config.write(file)

    def __init_base_services(self, is_debug):
        logger = Logger(is_debug, './../logs/')
        self.log = logger.log
        self.log('Program is launching')
        self.communicator = communicator.Communicator('../resources/config.ini', 'core', self.log)
        self.log('Base services are loaded')

    def __init_views(self):
        self.viewsManager = ViewsManager(self.log)
        self.viewsManager.init_views()

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
        self.__listener.listen()
