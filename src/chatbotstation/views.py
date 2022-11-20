import os, inspect, sys
from traceback import format_exc
from .templates import super_view
from .config import read_config, write_config


class _RawView:
    def __init__(self, log):
        self.log = log

    def report(self, message: str):
        self.log(message)


def import_view(name: str) -> super_view.SuperView:
    module = __import__(f'{__package__}.allviews.{name}.{name}')
    instance = getattr(getattr(getattr(getattr(module,
                                               'chatbotstation'),
                                       'allviews'),
                               name),
                       name)
    return instance


class ViewsManager:
    main_view = None
    views = {}

    def __init__(self, log, communicator):
        self.communicator = communicator
        self.log = log
        sys.path.insert(0, 'src/chatbotstation/allviews')

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
        self.main_view = _RawView(self.log)  # если ну прям вообще ничего нет, то всё уйдёт в логи

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
        failed_imports = {}

        for x in views_dir:
            try:
                imports.append(import_view(x))
                # imports.append(getattr(__import__(f'{x}.{x}'), x))
            except Exception as e:
                # msg = f'Exception in the import view module({x}):\n{str(type(e))}\n{str(e)}'
                msg = format_exc()
                self.error(msg)
        views = {}
        for x in imports:
            if x.__name__.split('.')[0] in disabled_views:
                continue
            found = False
            for cls in inspect.getmembers(x, inspect.isclass):
                view_name = x.__name__.split('.')[0]
                if super_view.SuperView in cls[1].__bases__ and cls[0].lower() == view_name:
                    try:
                        views[view_name] = cls[1](is_daemon=False)  # составляется словарь вьюшек вида { название : класс }
                    except Exception as e:
                        failed_imports[cls[1]] = str(e)
                    found = True
                    break
            if not found:
                msg = 'Can\'t import view ' + x + '. This file does not contain class that inherited from SuperView and names like view folder'
                self.error(msg)
        self.log(f'Loaded views: {str([x for x in views])}')
        self.views = views

        running_views = self.ping_views()
        if len(running_views):
            self.log(f'Running views now: {str(running_views)}')
        else:
            self.log('No running views now. Using Raw View from ViewsManager')
        views_to_start = set(views.keys()) - running_views - disabled_views - {'cliview'}

        if len(views_to_start) > 0:
            old_path = os.getcwd()
            os.chdir('allviews/') ########################
            for view in views_to_start:
                try:
                    os.system(f'nohup python3 -m {view} > ./{view}/logs/launchlogs.txt 2>&1 &')
                except:
                    continue
            os.chdir(old_path)
            self.log(str(views_to_start) + ' started')
        else:
            self.log('No views to start')

        if len(failed_imports):
            for imp in failed_imports:
                self.error('Failed import view: ' + str(imp) + '\nException: ' + str(failed_imports[imp]))

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
            if super_view.SuperView in cls[1].__bases__ and cls[0].lower() == view_name:
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
