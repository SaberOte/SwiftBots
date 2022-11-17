import communicator, config
from viewsmanager import ViewsManager
from pluginmanager import PluginManager
from logger import Logger
from listener import Listener


class BotBase:
    def __init__(self, is_debug: bool):
        config.fillconfig()
        self.__init_base_services(is_debug)
        self.__init_views()
        self.__init_plugins()
        self.__listener = Listener(self)

    def __init_base_services(self, is_debug: bool):
        logger = Logger(is_debug, './../logs/')
        self.log = logger.log
        logger.log("Program is launching")
        self.communicator = communicator.Communicator('core', self.log)
        logger.log('Base services are loaded')

    def __init_views(self):
        self.views_manager = ViewsManager(self.log, self.communicator)
        self.views_manager.init_views()
        self.report = self.views_manager.report
        self.error = self.views_manager.error

    def __init_plugins(self):
        self.plugin_manager = PluginManager(self)
        self.plugin_manager.init_plugins()

    def _start_(self):
        self.__listener.listen()
