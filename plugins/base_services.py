from superplugin import SuperPlugin, admin_only
import os, datetime, subprocess, random
from sys import platform

class BaseServices(SuperPlugin):
    def __init__(self, bot):
        super().__init__(bot)

    def send_menu(self):   
        self.sender.send_menu(self.user_id)

    def say_hi(self):
        self.sender.send_sticker(self.user_id, '21') #12116
    
    @admin_only
    def reboot(self):
        self.bot.sock.close()
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
        self.bot.sock.close()
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
        for app in self.bot.apps:
            status += '\n' + self._get_app_status(app) + '\n'
        self.sender.send(self.user_id, status)
    
    def _get_app_status(self, app=None):
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

    @admin_only
    def app_status(self, app=None):
        self.sender.send(self.user_id, self._get_app_status(app))

    @admin_only
    def update_apps(self):
        self.bot.update()

    @admin_only
    def show_apps(self):
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
    
    @admin_only
    def show_logs(self):
        if self.message == '':
            path_to_logs = './../logs/'
            filename = path_to_logs + sorted(os.listdir(path_to_logs))[-1]
            with open(filename, 'r') as file:
                self.sender.send(self.user_id, file.read()[-12000:])
            return
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

    @admin_only
    def launch_app(self):
        for app in self.bot.apps:
            if self.message == app.name:
                if app.is_enabled == True and self.bot.check_connection(app):
                    self.log("It's try to launch app that is already enabled")
                    self.sender.send(self.user_id, 'App already is running')
                    return
                self.log('Launching app %s...' % app.name)
                old_path = os.getcwd()
                try:
                    if platform == 'linux':
                        bot_name = old_path.split('/')[-2]
                        os.chdir('./../apps/')
                        subprocess.Popen(['python3', app.folder, '{%s}'%bot_name])
                    elif platform == 'win32':
                        os.chdir('.\\..\\apps\\')
                        subprocess.Popen('python %s' % app.folder)
                except Exception as e:
                    os.chdir(old_path)
                    raise e
                os.chdir(old_path)
                self.log('App is launched')
                return
        self.log('!!ERROR!!\nNo app with such name "%s"' % self.message)
        if self.user_id != self.keys.admin_id:
            self.sender.send(user_id, 'Нет приложения "%s"' % self.message)
        self.sender.report('Нет приложения "%s"' % self.message)

    @admin_only
    def auto_commands(self):
        answer = ''
        answer += 'Plugins:\n'
        for x in self.bot.plugins:
            answer += '- '+x.__class__.__name__+'\n'
            if len(x.cmds) > 0:
                answer += 'commands: '
                answer += ', '.join(list(x.cmds.keys()))
                answer += '\n'
            if len(x.prefixes) > 0:
                answer += 'prefixes: '
                answer += ', '.join(list(x.prefixes.keys()))
                answer += '\n'

        answer += 'Apps:\n'
        for x in self.bot.apps:
            answer += '- '+x.name+'\n'
            if len(x.cmds) > 0:
                answer += 'commands: '
                answer += ', '.join(list(x.cmds.keys()))
                answer += '\n'
            if len(x.prefixes) > 0:
                answer += 'prefixes: '
                answer += ', '.join(list(x.prefixes.keys()))
                answer += '\n'
        self.sender.send(self.user_id, answer)

    prefixes = {
            "launch" : launch_app,
            "start" : launch_app,
            "status" : app_status,
            "logs" : show_logs,
            "логи" : show_logs
            }
    cmds = {
        "команды" : send_menu,
        "привет" : say_hi,
        "доброе утро" : say_hi,
        "hi" : say_hi,
        "hello" : say_hi,
        "хай" : say_hi,
        "хаюшки" : say_hi,
        "приветики" : say_hi,
        "ку" : say_hi,
        "q" : say_hi,
        "здравствуйте" : say_hi,
        "здрасьте" : say_hi,
        "update" : update_apps,
        "выход" : exit,
        "exit" : exit,
        "выключить" : exit,
        "отключить" : exit,
        "иди нахер" : exit,
        "пошел в очко" : exit,
        "отсоси" : exit,
        "иди нахуй" : exit,
        "умри" : exit,
        "status" : common_status,
        "перезагрузить" : reboot,
        "перезапустить" : reboot,
        "reboot" : reboot,
        "ребут" : reboot,
        "apps" : show_apps,
        "приложения" : show_apps,
        "автокоманды" : auto_commands,
        "autocommands" : auto_commands
    }
    

