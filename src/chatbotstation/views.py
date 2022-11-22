import os, inspect, sys
from typing import Union
from traceback import format_exc
from .templates.super_view import SuperView
from .config import read_config, write_config
from .communicators import Communicator
import subprocess

'''
проблемы:
main_view назначается до запуска остальных
update view пока не работает
'''


class _RawView:
    def __init__(self, log):
        self.log = log

    def report(self, message: str):
        self.log(message)


def launch_view(name: str, flags: list[str]):
    check_valid(name)
    if 'machine start' in flags:  # direct start
        try:
            module = import_view(name)
            clas = get_class(module)
            inst = clas()
            flags.append('launch')
            inst.init(flags)
            inst.init_listen()
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


def check_valid(name: str):
    """Check existence view file and its correct name"""
    if name not in os.listdir('src/chatbotstation/allviews'):
        raise Exception(f"Directory src/chatbotstation/{name} doesn't exist")
    if f'{name}.py' not in os.listdir(f'src/chatbotstation/allviews/{name}'):
        raise Exception(f"Module src/shatbostation/{name}/{name} doesn't exist")


def get_class(module) -> any:
    for cls in inspect.getmembers(module, inspect.isclass):
        if SuperView in cls[1].__bases__:
            return cls[1]
    msg = f"Can't import view {module.__name__.split('.')[0]}. This file does not contain " \
          'class that inherited from SuperView'
    raise ImportError(msg)


def import_view(name: str):
    module = __import__(f'{__package__}.allviews.{name}.{name}')
    instance = getattr(getattr(getattr(getattr(module,
                                               'chatbotstation'),
                                       'allviews'),
                               name),
                       name)
    return instance


class ViewsManager:
    main_view: Union[SuperView, _RawView]
    views: {str: SuperView} = {}

    def __init__(self, log, communicator, flags):
        self.communicator = communicator
        self.log = log
        self.flags = flags
        self.main_view = _RawView(lambda x: None if 'debug' in flags else log)

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
            self.main_view = _RawView(lambda x: None if 'debug' in self.flags else self.log)
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

    def ping_view(self, view: str):
        config = read_config()
        if view not in config['Names']:
            return False
        ans = self.communicator.request('ping', view)
        if ans and ans['message'] == 'pong':
            return True
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

        views_dir = \
            [x for x in os.listdir('src/chatbotstation/allviews')
             if x.endswith('_view')
             and x.islower()
             and x not in disabled_views
             and not x.startswith('__')]
        imports = []

        for x in views_dir:
            try:
                imports.append(import_view(x))
            except Exception as e:
                # msg = f'Exception in the import view module({x}):\n{str(type(e))}\n{str(e)}'
                msg = format_exc()
                self.error(msg)

        for x in imports:
            view_name = x.__name__.split('.')[-1]
            try:
                clas = get_class(x)()
                clas.init([])
                clas.log = self.log
                # составляется словарь вьюшек вида { название : класс }
                self.views[view_name] = clas
            except Exception as e:
                self.log(str(e))
                self.error(f'Module {view_name} failed to import: {e}')

        self.log(f'Loaded views: {[x for x in self.views]}')

        running_views = self.ping_views()
        if len(running_views) > 0:
            self.log(f'Running views now: {running_views}')
        else:
            self.log('No running views now. Using Raw View from ViewsManager')
        views_to_start = set(self.views.keys()) - running_views - disabled_views - {'cliview'}

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

    def update_view(self, view: str) -> int:
        module = [x for x in os.listdir('/views') if x.endswith('view') and x.islower() and x == view]
        if len(module) == 0:
            return 0
        module = module[0]
        try:
            imported = import_view(module)
            # imported = getattr(__import__(f'{module}.{module}'), module)
        except Exception as e:
            msg = f'Exception in the import view module({module}):\n{str(type(e))}\n{str(e)}'
            raise Exception(msg)
        config = read_config()
        disabled_views = set(config['Disabled_Views'])
        self.log(f'Disabled views: {str(disabled_views)}')
        found = False
        view_key = None
        for cls in inspect.getmembers(imported, inspect.isclass):
            view_name = imported.__name__.split('.')[0]
            if SuperView in cls[1].__bases__ and cls[0].lower() == view_name:
                try:
                    self.views[view_name] = cls[1](is_daemon=False)
                except Exception as e:
                    raise Exception(f'Failed to instantiate view {view}:\n{str(type(e))}\n{str(e)}')
                found = True
                break
        if not found:
            msg = 'Can\'t import view ' + view + '. This file does not contain class that inherited from SuperView and names like view folder'
            self.error(msg)
        self.log(f'Updated internal view: {view}')

        running_views = self.ping_views()
        if len(running_views):
            self.log(f'Running views now: {str(running_views)}')
        else:
            self.log('No running views now')
        if view in running_views:
            old_path = os.getcwd()
            os.chdir('./../views/')  #######################
            try:
                os.system(f'nohup python3 {view} > ./{view}/logs/launchlogs.txt 2>&1 &')
            except Exception as e:
                os.chdir(old_path)
                raise Exception(f'View {view} failed to start!!\n{type(str(e))}\n{e}')
            os.chdir(old_path)
            self.log(str(view) + ' started')
            return 2
        else:
            self.log('View is not needed to start')
            return 1
