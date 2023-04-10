from traceback import format_exc
import os
from . import communicators
from .views import ViewsManager
from .controllers import ControllerManager
from .logger import Logger
from .listener import Listener
from typing import Callable


def launch_bot(flags: list[str]):
    """start core instance"""
    if 'debug' in flags or 'machine start' in flags:  # direct start
        bot = Core(flags)
        bot.init()
        try:
            if 'from reboot' in flags:
                bot.views_manager.report('Core is restarted!')
            else:
                bot.views_manager.report('Core is launched')
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
    else:  # launch daemon instance
        res_path = os.path.join(os.getcwd(), 'logs')
        os.system('nohup python3 main.py @botcore_core@ '
                  f'start -MS > {res_path}/core_launch_log.txt 2>&1 &')


class Core:
    """keks"""
    __listener: Listener
    controller_manager: ControllerManager
    views_manager: ViewsManager
    report: Callable
    error: Callable
    log: Callable

    def __init__(self, flags: list[str]):
        self.flags = flags
        self.__init_base_services()

    def init(self):
        self.__init_views()
        self.__init_controllers()
        self.__listener = Listener(self)

    def __init_base_services(self):
        logger = Logger('core', 'debug' in self.flags)
        self.log = logger.log
        logger.log("Program is launching")
        self.communicator = communicators.Communicator('core', self.log)
        logger.log('Base services are loaded')

    def __init_views(self):
        self.views_manager = ViewsManager(self.log, self.communicator, self.flags)
        self.views_manager.init_views()
        self.report = self.views_manager.report
        self.error = self.views_manager.error

    def __init_controllers(self):
        self.controller_manager = ControllerManager(self)
        self.controller_manager.init_controllers()

    def start(self):
        self.__listener.listen()
