from traceback import format_exc
import sys
import os
from . import communicators
from . import config
from .views import ViewsManager
from .plugins import PluginManager
from .logger import Logger
from .listener import Listener


def launch_bot(flags: list[str]):
    """start core instance"""
    if 'debug' in flags or 'machine_start' in flags:  # direct start
        bot = Core(flags)
        bot.init()
        try:
            if 'from_reboot' in flags:
                bot.views_manager.report('Бот перезапущен')
        except:
            pass
        try:
            bot.start()
        except:
            msg = format_exc()
            if bot.error:
                bot.error(msg)
            else:
                print(msg)
            sys.exit(1)
    else:  # launch daemon instance
        res_path = os.path.join(os.getcwd(), 'resources')
        os.system('nohup python3 -m main.py {chatbotstation_core} start -MS > '
                  f'{res_path}/launch_log.txt 2>&1 &')
        sys.exit(0)


class Core:
    __listener: Listener

    def __init__(self, flags: list[str]):
        self.flags = flags
        config.fill_config()
        self.__init_base_services()

    def init(self):
        self.__init_views()
        self.__init_plugins()
        self.__listener = Listener(self)

    def __init_base_services(self):
        logger = Logger('core', 'debug' in self.flags)
        self.log = logger.log
        logger.log("Program is launching")
        self.communicator = communicators.Communicator('core', self.log)
        logger.log('Base services are loaded')

    def __init_views(self):
        self.views_manager = ViewsManager(self.log, self.communicator)
        self.views_manager.init_views()
        self.report = self.views_manager.report
        self.error = self.views_manager.error

    def __init_plugins(self):
        self.plugin_manager = PluginManager(self)
        self.plugin_manager.init_plugins()

    def start(self):
        self.__listener.listen()
