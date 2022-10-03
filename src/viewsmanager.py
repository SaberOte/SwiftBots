import os, subprocess, inspect, superview
from config import readconfig, writeconfig


class RawView:
    def __init__(self, log):
        self.log = log

    def report(self, message):
        self.log(message)


class ViewsManager:
    main_view = None

    def error(self, message):
        self.log('!!!ERROR!!!\n'+str(message))
        self.report(message)

    def report(self, message):
        # можно ещё сделать накопление ошибок или передачу их другой вьюшке
        if not self.main_view:
            self.assign_main_view()
        self.main_view.report(message)

    def assign_main_view(self):
        if len(self.views) == 0:
            self.main_view = RawView(self.log)
            return
        config = readconfig()
        disabled_views = set(config['Disabled_Views'])
        main_views = list(config['Main_View'])
        loaded_views = self.views
        if len(main_views) > 0:
            view = main_views[0]
            if view in loaded_views and view not in disabled_views and self.ping_view(view):
                self.main_view = view
                return
        for view in loaded_views:
            if view != 'cliview' and view not in disabled_views and self.ping_view(view):
                self.main_view = loaded_views[view]
                return
        if 'cliview' in loaded_views and 'cliview' not in disabled_views and self.ping_view('cliview'):
            self.main_view = loaded_views['cliview']
            return
        self.main_view = RawView(self.log)

    def __init__(self, log, communicator):
        self.communicator = communicator
        self.log = log

    def ping_view(self, view):
        ans = self.communicator.request('ping', view)
        if ans and ans['message'] == 'pong':
            return True
        return False

    def ping_views(self):
        config = readconfig()
        disabled_views = set(config['Disabled_Views'])
        active_views = set(filter(lambda x: x.endswith('view'), config['Names'])) - disabled_views
        running_views = set()
        for view in active_views:
            if self.ping_view(view):
                running_views.add(view)
        return running_views

    def init_views(self):
        views_dir = [x for x in os.listdir('../views') if x.endswith('view')]
        imports = []
        for x in views_dir:
            try:
                imports.append(getattr(__import__(f'{x}.{x}'), x))
            except Exception as e:
                msg = f'Exception in the import view module({x}):\n{str(type(e))}\n{str(e)}'
                self.log(msg)
                ###### self.sender.report(msg)
        views = {}
        for x in imports:
            found = False
            for cls in inspect.getmembers(x, inspect.isclass):
                view_name = x.__name__.split('.')[0]
                if superview.SuperView in cls[1].__bases__ and cls[0].lower() == view_name:
                    views[view_name] = cls[1]  # составляется словарь вьюшек вида { название : класс }
                    found = True
                    break
            if not found:
                msg = 'Can\'t import view ' + x + '. This file does not contain class that inherited from SuperView and names like view folder'
                self.log(msg)
                ###### self.sender.report(msg)
        self.log(f'Loaded views: {str(views)}')
        self.views = views

        config = readconfig()
        disabled_views = set(config['Disabled_Views'])
        running_views = self.ping_views()
        views_to_start = set(views.keys()) - running_views - disabled_views

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
        else:
            self.log('No views to start')
