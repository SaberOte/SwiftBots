from superplugin import SuperPlugin, admin_only
import os, datetime, subprocess, cronmanager
from sys import platform

class BaseServices(SuperPlugin):
    def __init__(self, bot):
        super().__init__(bot)

    def send_menu(self):   
        self.sender.send_menu(self.user_id)

    def say_hi(self):
        self.sender.send_sticker(self.user_id, '21')
    
    @admin_only
    def reboot(self):
        if platform == 'linux':
            subprocess.Popen(['python3','./../upbot.py'])
        elif platform == 'win32':
            subprocess.Popen('python ..\\upbot.py')
        else:
            self.sender.send(self.user_id, 'Эта OC не поддерживается. Перезапуска не будет')
        self.log('Program is rebooting')
        self.exit()

    @admin_only
    def exit(self):
        if self.user_id != self.keys.admin_id:
            self.sender.report('Бот остановлен.')
        self.sender.send(self.user_id, 'Бот остановлен.')
        self.log('Program is suspended')
        os._exit(1)
        
    @admin_only
    def common_status(self):
        status = ''
        dt = datetime.datetime.utcnow()-self.start_time
        if dt.days == 0:
            if dt.seconds < 60:
                dt = str(dt.seconds) + " секунд"
            elif dt.seconds < 60*60:
                dt = str(dt.seconds//60) + " минут"
            else:
                dt = str(dt.seconds//60//60) + " часов"
        elif dt.days < 7:
            dt = str(dt.days) + " дней"
        elif dt.days < 30:
            dt = str(dt.days // 7) + " недель"
        elif dt.days < 365:
            dt = str(dt.days//30) + " месяцев"
        else: dt = str(dt.days//365) + " лет"
        status += f'С запуска бота прошло {dt}\n' 
        #for app in self.bot.apps: #########
        #    status += '\n' + self._get_app_status(app) + '\n' ##############
        self.sender.send(self.user_id, status)
    
    def _get_app_status(self, app=None):
        pass
        ###############
        '''
        if app == None:
            for a in self.bot.apps:
                if a.name == self.message:
                    app = a
        if app == None:
            self.log(f'App with such name "{self.message}" is not found')
            self.sender.send(self.user_id, f'Нет приложения с названием "{self.message}"')
            return
        self.bot.check_connection(app)
        info = None
        if app.is_enabled == False:
            respond = app.name+' неактивен&#9898;\n'
        else:
            ans = self.bot.send_to_port('is_running', app, 0.4, 32)
            if ans == "True":
                respond = app.name+' активен&#128640;\n'
                info = self.bot.send_to_port('get_info', app, 5, 8192)
            elif ans == "False":
                respond = app.name+' ожидает&#129517;\n'
                info = self.bot.send_to_port('get_info', app, 5, 8192)
            else:
                self.log('Uncorrect answer "is_running"')
                respond = 'Uncorrect answer "is_running"'
        if info != None:
            respond += info
        return respond
        '''

    @admin_only
    def app_status(self, app=None):
        ################
        #self.sender.send(self.user_id, self._get_app_status(app))
        pass

    @admin_only
    def show_apps(self):
        pass
        #########
        '''
        active = []
        waiting = []
        non_active = []
        for app in self.bot.apps:
            self.bot.check_connection(app)
            if app.is_enabled:
                is_running = self.bot.send_to_port('is_running', app, 1, 32) 
                if is_running == "True":
                    active.append(app.name)
                elif is_running == "False":
                    waiting.append(app.name)
                else:
                    self.log('Uncorrect answer "is_running"')
                    self.sender.report('Uncorrect answer "is_running"')
            else:
                non_active.append(app.name)
        report = ''
        if len(active) > 0:
            report += 'Активные службы:\n'
            for x in active:
                report += '- '+x+'&#128640;\n' # ракета 
        if len(waiting) > 0:
            report += 'В режиме ожидания:\n'
            for x in waiting:
                report += '- '+x+'&#129517;\n' # часики 
        if len(non_active) > 0:
            report += 'Неактивные:\n'
            for x in non_active:
                report += '- '+x+'&#9898;\n' # пусто
        self.sender.send(self.user_id, report)
        '''
    
    @admin_only
    def show_logs(self):
        if self.message == '':
            path_to_logs = './../logs/'
            filename = path_to_logs + sorted(os.listdir(path_to_logs))[-1]
            with open(filename, 'r') as file:
                self.sender.send(self.user_id, file.read()[-12000:])
            return
        ''' ##############
        app = None
        for a in self.bot.apps:
            if a.name == self.message:
                app = a
        if app == None:
            self.log('No app with such name %s' % self.message)
            self.sender.send(self.user_id, f'Нет приложения с названием "{self.message}"')
            return
        folder = app.folder
        path_to_logs = f'./../apps/{folder}/logs/'
        filename = path_to_logs + sorted(os.listdir(path_to_logs))[-1]
        with open(filename, 'r', encoding='utf-8') as file:
            self.sender.send(self.user_id, file.read()[-12000:])
        '''

    @admin_only
    def auto_commands(self):
        answer = ''
        for x in self.bot.plugins:
            answer += '- '+x.__class__.__name__+'\n'
            if len(x.cmds) > 0:
                answer += 'COMMANDS: '
                answer += ', '.join(list(x.cmds.keys()))
                answer += '\n'
            if len(x.prefixes) > 0:
                answer += 'PREFIXES: '
                answer += ', '.join(list(x.prefixes.keys()))
                answer += '\n'

        self.sender.send(self.user_id, answer)

    @admin_only
    def schedule_task(self):
      task = self.message
      plugin = None
      for plug in self.bot.plugins:
        if task in plug.tasks:
          plugin = plug
      if plugin == None:
        all_tasks = []
        for plug in self.bot.plugins:
          for x in plug.tasks:
            all_tasks.append(x)
        self.sender.send(self.user_id, 'Такой задачи нет. Все задачи: ' + ', '.join(all_tasks))
        self.log(f'Unknown task {task} is called')
        return
      delay = plugin.tasks[task][1]
      path = os.path.split(os.getcwd())[0]
      cronmanager.add(plugin.__class__.__name__, task, delay, path)
      self.log(f'Task {task} is scheduled')
      self.sender.send(self.user_id, 'Задача запущена')

    @admin_only
    def unschedule_task(self):
      pass

    prefixes = {
            "status" : app_status,
            "logs" : show_logs,
            "логи" : show_logs,
            "start" : schedule_task,
            "stop" : unschedule_task,
            }
    cmds = {
        "команды" : send_menu,
        "привет" : say_hi,
        "hi" : say_hi,
        "hello" : say_hi,
        #"update" : update_apps,
        "выход" : exit,
        "exit" : exit,
        "выключить" : exit,
        "stop" : exit,
        "status" : common_status,
        "перезагрузить" : reboot,
        "перезапустить" : reboot,
        "reboot" : reboot,
        "ребут" : reboot,
        #"apps" : show_apps,
        #"приложения" : show_apps,
        "автокоманды" : auto_commands,
        "autocommands" : auto_commands
    }
