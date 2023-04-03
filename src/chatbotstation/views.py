import os, inspect, sys, importlib
from types import ModuleType
from typing import Union
from traceback import format_exc
from .templates.super_view import SuperView
from .config import read_config, write_config
from .communicators import Communicator
import subprocess


class _RawView:
    def __init__(self, log):
        self.log = log

    def report(self, message: str):
        message = '---Raw View report:\n' + message + '\n---'
        self.log(message)


def launch_view(name: str, flags: list[str]):
    """
    Looking at flags, launches a view as a daemon or as a main thread (LOCKS FURTHER CODE)
    :param name: exact view name
    :param flags: see flags description in __main__.py
    """
    check_name_valid(name)
    if 'machine start' in flags:  # direct start
        try:
            module = import_view(name)
            module = importlib.reload(module)  # if program was updated and restarted
            clas = get_class(module)
            inst: SuperView = clas()
            flags.append('launch')
            inst.init(flags)
            inst.init_listen()  # Starts infinite loop and never return
        except:
            comm = Communicator(name+'ghost', print)
            try:
                msg = f'Exception in view launching:\n{format_exc()}'
                comm.send('report|' + msg, 'core')
            finally:
                comm.close()
    else:  # start as daemon
        res_path = os.path.join(os.getcwd(), 'logs')
        if 'debug' in flags:
            '''try:
                module = import_view(name)
                clas = get_class(module)
                inst = clas()
                inst.init(['launch', 'debug'])
                inst.init_listen()
            except:
                print(format_exc())
            '''
            # os.system(f'python3 main.py @chatbotstation_{name}@ '
            #          f'start {name} -MS -d')
            cmd = f'python3 main.py @chatbotstation_{name}@ ' \
                  f'start {name} -MS -d'
            subprocess.Popen(cmd.split(' '))
        else:
            os.system(f'nohup python3 main.py @chatbotstation_{name}@ '
                      f'start {name} -MS > {res_path}/{name}_launch_log.txt 2>&1 &')


def check_name_valid(name: str):
    """Check existence view file and its correct name"""
    assert name in os.listdir('src/chatbotstation/allviews'), \
        f"Directory src/chatbotstation/allviews/{name} doesn't exist"
    assert f'{name}.py' in os.listdir(f'src/chatbotstation/allviews/{name}'), \
        f"Module src/shatbostation/allviews/{name}/{name} doesn't exist"
    assert name.islower(), 'View name must be lowercase'
    assert name.endswith('view'), 'View name must end with "view"'


def get_class(module: ModuleType):
    for cls in inspect.getmembers(module, inspect.isclass):
        if SuperView in cls[1].__bases__:
            return cls[1]
    msg = f"Can't import view {module.__name__.split('.')[0]}. This file does not contain " \
          'class that inherited from SuperView'
    raise ImportError(msg)


def import_view(name: str) -> ModuleType:
    module = __import__(f'{__package__}.allviews.{name}.{name}')
    instance = getattr(getattr(getattr(getattr(module,
                                               'chatbotstation'),
                                       'allviews'),
                               name),
                       name)
    return instance


class ViewsManager:
    main_view: Union[SuperView, _RawView, None]
    views: {str: SuperView} = {}

    def __init__(self, log, communicator: Communicator, flags):
        self.communicator = communicator
        self.log = log
        self.flags = flags
        # self.main_view = _RawView(lambda x: None if 'debug' in flags else log)
        self.main_view = None # _RawView(log)

    def error(self, message: str):
        self.log('!!!ERROR!!!\n'+str(message))
        self.report(str(message))

    def report(self, message: str):
        # можно ещё сделать накопление ошибок или передачу их другой вьюшке
        if not self.main_view:
            self.assign_main_view()
        self.log('Report has sent to main view : ' + self.main_view.__class__.__name__)
        self.main_view.report(str(message))

    def assign_main_view(self):
        if len(self.views) == 0:
            # self.main_view = _RawView(lambda x: None if 'debug' in self.flags else self.log)
            self.main_view = _RawView(self.log)
            return
        config = read_config()
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
        self.main_view = _RawView(lambda x,y: None if 'debug' in self.flags else self.log)  # если ну прям вообще ничего нет, то всё уйдёт в логи

    def ping_view(self, view: str) -> bool:
        """
        Pings a view to detect it's active and responds
        :param view: view name
        :return: False if view isn't the list in cofing, or it doesn't respond. True if it responds
        """
        config = read_config()
        if view not in config['Names']:
            return False
        comm = Communicator('core' + 'ghost', self.log)
        ans = comm.request('ping', view)
        comm.close()
        if ans and ans['message'] == 'pong':
            return True
        # View is not responded. Then delete it from config
        config = read_config()
        if view in config['Names']:
            del config['Names'][view]
            write_config(config)
        return False

    def ping_views(self) -> set:
        config = read_config()
        disabled_views = set(config['Disabled_Views'])
        active_views = set(filter(lambda x: x.endswith('view'), config['Names'])) - disabled_views
        running_views = set()
        for view in active_views:
            if self.ping_view(view):
                running_views.add(view)
        return running_views

    def init_views(self):
        config = read_config()
        disabled_views = set(config['Disabled_Views'])
        self.log(f'Disabled views: {str(disabled_views)}')

        # receiving modules NAMES
        views_dir: list[str] = \
            [x for x in os.listdir('src/chatbotstation/allviews')
             if x.endswith('_view')
             and x.islower()
             and x not in disabled_views
             and not x.startswith('!')]

        self.__fill_views_dict(views_dir)
        self.log(f'Loaded views: {[x for x in self.views]}')

        # Detecting of already running views
        running_views: set[str] = self.ping_views()
        if len(running_views) > 0:
            self.log(f'Running views now: {running_views}')
        else:
            self.log('No running views now. Using Raw View from ViewsManager')

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
            self.log('No views to start')
        else:
            self.log(str(started) + ' started')

    def __fill_views_dict(self, views_dir: list[str], should_reload=False) -> int:
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
                clas: SuperView = get_class(x)()
                clas.init([])  # with no flags
                clas.log = self.log
                # Setting dict of views as { name : class }
                self.views[view_name] = clas
                counter += 1
            except Exception as e:
                self.log(str(e))
                self.error(f'Module {view_name} failed to import: {e}')
        return counter

    def update_view(self, view: str) -> int:
        """
        Updates all methods for core and sends request for view to be updated itself. It's no any reboots
        :param view: view name
        :return: int, 0 - nothing updated, 1 - updated in the core, but it's not launched, 2 - updated in the core and itself
        """
        check_name_valid(view)
        updated = self.__fill_views_dict([view], True)
        if updated:
            if self.ping_view(view):
                self.communicator.send('update', view)
                return 2
            return 1
        return 0

