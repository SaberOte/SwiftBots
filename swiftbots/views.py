import os
from sys import stderr
import importlib
from types import ModuleType
from typing import Union
from traceback import format_exc
from swiftbots import BaseView
from swiftbots.config import read_config, write_config
from swiftbots import Communicator


class _RawView:
    def report(self, message: str):
        message = '---Raw View report:\n' + message + '\n---'
        print(message)

'''
def launch_view(name: str):
    """
    Launches a view by name.
    :param name: exact view name
    """
    check_name_valid(name)
    module = import_view(name)
    instance: BaseView = get_class(module)()
    instance.init()
    instance.init_listen()  # Starts infinite loop and never return

def check_name_valid(name: str):
    """Check existence view file and its correct name"""
    assert f'{name}.py' in os.listdir(f'views'), \
        f"Module views/{name}.py doesn't exist"
    assert not name.startswith('!'), 'View with ! char is deactivated'


def get_class(module: ModuleType):
    for cls in inspect.getmembers(module, inspect.isclass):
        if issubclass(cls[1], BaseView) and ABC not in cls[1].__bases__:
            return cls[1]
    raise ImportError(
        f"Can't import view {module.__name__.split('.')[0]}. This file does not contain "
         'class that inherited from BaseView')


def import_view(name: str) -> ModuleType:
    module = __import__(f'views.{name}')
    instance = getattr(module, name)  # get name instead of views.name
    return instance
'''

class ViewsManager:
    main_view: Union[BaseView, _RawView, None]
    views: {str: BaseView} = {}

    def __init__(self, communicator: Communicator, flags):
        self.communicator = communicator
        self.flags = flags
        # self.main_view = _RawView()
        self.main_view = None

    def error(self, message: str):
        print(message, file=stderr)
        self.report(str(message))

    def report(self, message: str):
        raise NotImplementedError(message)
        if not self.main_view:
            self.assign_main_view()
        print('Report has sent to main view : ' + self.main_view.__class__.__name__)
        self.main_view.report(str(message))

    def assign_main_view(self):
        if len(self.views) == 0:
            # self.main_view = _RawView(lambda x: None if 'debug' in self.flags else print)
            self.main_view = _RawView()
            return
        config = read_config('config.ini')
        disabled_views = set(config['Disabled_Views'])
        main_views = list(config['Main_View'])
        loaded_views = self.views
        if len(main_views) > 0:  # сначала берётся из конфига основной репортер
            view = main_views[0]
            if view in loaded_views and view not in disabled_views:
                self.main_view = loaded_views[view]
                return
        for view in loaded_views:  # если основной репортер недоступен/отсутствует, то берётся первый попавшийся
            if view != 'cliview' and view not in disabled_views:  # избегаю cliview
                self.main_view = loaded_views[view]
                return
        if 'cliview' in loaded_views and 'cliview' not in disabled_views and self.ping_view('cliview'):  # если только cliview есть, выбирается он
            self.main_view = loaded_views['cliview']
            return
        self.main_view = _RawView()

    def ping_view(self, view: str) -> bool:
        """
        Pings a view to detect it's active and responds
        :param view: view name
        :return: False if view isn't the list in cofing, or it doesn't respond. True if it responds
        """
        config = read_config('config.ini')
        if view not in config['Names']:
            return False
        comm = Communicator('core' + 'ghost')
        try:
            ans = comm.request('ping', view)
        finally:
            comm.close()
        if ans and ans['message'] == 'pong':
            return True
        # View is not responded. Then delete it from config
        config = read_config('config.ini')
        if view in config['Names']:
            del config['Names'][view]
            write_config(config, 'config.ini')
        return False

    def ping_views(self) -> set:
        config = read_config('config.ini')
        disabled_views = set(config['Disabled_Views'])
        # active_views = set(filter(lambda x: x.endswith('view'), config['Names'])) - disabled_views
        active_views = set(config['Names']) - disabled_views
        running_views = set()
        for view in active_views:
            if self.ping_view(view):
                running_views.add(view)
        return running_views

    def init_views(self):
        config = read_config('config.ini')
        disabled_views = set(config['Disabled_Views'])
        print(f'Disabled views: {str(disabled_views)}')

        # receiving modules NAMES
        views_dir: list[str] = \
            [x[:-3] for x in os.listdir('views')
             if x.islower()
             # and x.endswith('view.py')
             and x[:-3] not in disabled_views
             and not x.startswith('!')]

        self.fill_views_dict(views_dir)
        print(f'Loaded views: {[x for x in self.views]}')

        # Detecting of already running views
        running_views: set[str] = self.ping_views()
        if len(running_views) > 0:
            print(f'Running views now: {running_views}')
        else:
            print('No running views now. Using Raw View from ViewsManager')

        # Starting of instances as daemons
        views_to_start: set[str] = set(self.views.keys()) - running_views - disabled_views - {'cliview'}
        started = []
        for view in views_to_start:
            view_flags = []
            if 'debug' in self.flags:
                view_flags.append('debug')
            try:
                launch_view(view, view_flags)
                started.append(view)
            except Exception as e:
                self.error(f'View {view} failed to start: {e}')

        if len(views_to_start) == 0:
            print('No views to start')
        else:
            print(str(started) + ' started')

    def fill_views_dict(self, views_dir: list[str], should_reload=False) -> int:
        """
        Fills self.views dict with views from views_dir list
        :param views_dir: names of views to instantiate
        :param should_reload: if view instantiates not first time it should be reloaded
        :return: number of inserted views
        """
        # importing as MODULES
        imports: list[ModuleType] = []
        for x in views_dir:
            try:
                imported = import_view(x)
                if should_reload:
                    importlib.reload(imported)
                imports.append(imported)
            except Exception as e:
                msg = "Exception in the import view module:\n" + format_exc()
                self.error(msg)

        # Filling self.views with view instances
        counter = 0
        for x in imports:
            view_name = x.__name__.split('.')[-1]
            try:
                clas: BaseView = get_class(x)()
                clas.init([])  # with no flags
                # Setting dict of views as { name : class }
                self.views[view_name] = clas
                counter += 1
            except Exception as e:
                print(str(e))
                self.error(f'Module {view_name} failed to import: {e}')
        return counter

    def update_view(self, view: str) -> int:
        """
        Updates all methods for core and sends request for view to be updated itself. It's no any reboots
        :param view: view name
        :return: int, 0 - nothing updated, 1 - updated in the core, but it's not launched, 2 - updated in the core and itself
        """
        check_name_valid(view)
        updated = self.fill_views_dict([view], True)
        if updated:
            if self.ping_view(view):
                self.communicator.send('update', view)
                return 2
            return 1
        return 0

    def kill_view(self, view: str) -> int:
        """
        Sends view an asking to exit itself
        :param view: view name
        :return: int, 0 - view is not launched, 1 - not exited. Reason is unknown., 2 - exited succesfully
        """
        if self.ping_view(view):
            comm = Communicator('core' + 'ghost')
            try:
                ans = comm.request('exit', view)
            finally:
                comm.close()
            if ans and ans['message'] == 'exited':
                return 2
            return 1
        return 0

