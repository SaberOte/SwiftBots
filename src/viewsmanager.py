import os, subprocess, inspect, superview, configparser


class RawView:
    def __init__(self, log):
        self.log = log

    def report(self, message):
        self.log(message)

class ViewsManager:
    main_view = None
    def report(self, message):
        self.main_view.report(message)

    def assign_main_view(self):
        if len(self.views) == 0:
            self.main_view = RawView(self.log)
        elif len(self.views) > 1:
            config = configparser.ConfigParser()
            config.read('../resources/config.ini')
            last_views = list(map(lambda x: x[0], config.items('Last_Views')))
            print(last_views)
            exit(1)
            '''остановился здесь. нужна функция для пропингивания всех вьюшек, а затем алгоритм для постановки основной вьюшки'''

        elif len(self.views) > 1 and self.views[0][0] == 'cliview':  # избегать cliview
            self.main_view = self.views[1][1]
        else:
            self.main_view

    def __init__(self, log):
        self.log = log

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
        self.log(f'Loaded views: {str(views)}')
        self.views = views

        config = configparser.ConfigParser()
        config.read('../resources/config.ini')
        disabled_views = set(map(lambda x: x[0], config.items('Disabled_Views')))
        active_views = set(filter(lambda x: x[0].endswith('view'), config.items('Names')))
        active_views = set(map(lambda x: x[0], active_views)) - disabled_views
        running_views = set()
        for view in active_views:
            ans = self.communicator.request('ping', view)
            if ans and ans['message'] == 'pong':
                running_views.add(view)
        views_to_start = set(map(lambda x: x[0], views)) - running_views - disabled_views

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
        return views
