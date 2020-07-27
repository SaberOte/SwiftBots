import os, time, datetime, requests, sys, inspect, socket, threading, ast
from keys import KeyManager
from msgsender import Sender
from superplugin import SuperPlugin
from listener import Listener
from apimanager import ApiManager
from logger import Logger

class BotBase:
    plugins = []
    def __init__(self, is_debug):
        self.__init_base_services(is_debug)
        self.__init_plugins()
        self.__init_apps()
        self.last_msg = time.time()
        self.__monitoring_thread = threading.Thread(target=self.monitor_apps, daemon=True)
        self.__monitoring_thread.start()
        self.__listener = Listener(self)

    def __init_base_services(self, is_debug):
        logger = Logger(is_debug, './../logs/')
        self.log = logger.log
        self.log('Program is launching')
        self.keys = KeyManager('./../resources/data.json', logger.log)
        self.api = ApiManager(self.keys, logger.log)
        self.sender = Sender('./../resources/', self.keys, self.api, logger.log)
        self.start_time = datetime.datetime.utcnow()
        self.BOT_PORT = self.keys.bot_port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('localhost', self.BOT_PORT))
        self.__thread_listening_port = threading.Thread(target=self.__listen_port, daemon=True)
        self.__is_listen_port_sleeping = False
        self.__is_listen_port_listening = False
        self.__go_on_sleep = False
        self.__thread_listening_port.start()
        
        self.log('Base services are loaded')

    def __listen_port(self):
        self.__is_listen_port_sleeping = False
        self.log('Listening port %d...' % self.BOT_PORT)
        sock = self.sock
        #skip stuff

        sock.settimeout(0.1)
        while True:
            try:
                sock.recv(8192)
            except: break
        
        while True:
            sock.settimeout(60*60*6)
            try:
                try:
                    self.__is_listen_port_listening = True
                    msg, addr = sock.recvfrom(1024)
                    time.sleep(0.01)
                    self.__is_listen_port_listening = False
                    msg = msg.decode('utf-8')
                except socket.timeout: continue
                self.log(f'Received msg in ports listener from {addr}: {msg}')
                if msg == 'ping':
                    self.log(f'"pong" sending to {addr[1]}')
                    sock.sendto(b'pong', addr)
                elif msg == 'update':
                    threading.Thread(target=self.update, daemon=True).start()
                elif msg == 'exited':
                    for app in self.apps:
                        if app.port == addr[1]:
                            app.is_enabled = False
                            break
                elif msg == 'stop' and addr[1] == self.BOT_PORT:
                    self.__is_listen_port_sleeping = True
                    while self.__go_on_sleep:
                        time.sleep(0.1)
                    self.__is_listen_port_sleeping = False
                else:
                    self.log('unknown message')
            except Exception as e:
                self.sock.close()
                self.sender.report(f'Exception in ports listener:\n{str(type(e))}\n{str(e)}')
                self.log(f'!!ERROR!!\nException in ports listener:\n{str(type(e))}\n{str(e)}')
                break
    
    def __init_plugins(self):
        modules = [x[:-3] for x in os.listdir('./../plugins') if x.endswith('.py')]
        imports = []
        for x in modules:
            try:
                imports.append(__import__(x))
            except Exception as e:
                self.sender.report(f'Exception in the import module({x}):\n{str(type(e))}\n{str(e)}')
        self.log(f'Imported modules: {str(modules)}')
        all_classes = []
        for x in imports:
            for cls in inspect.getmembers(x, inspect.isclass):
                if SuperPlugin in cls[1].__bases__:
                    all_classes.append(cls[1])
        classes = []
        for x in all_classes:
            if x not in classes:
                classes.append(x)
        self.log(f'Loaded classes: {str(classes)}')
        for x in classes:
            self.plugins.append(x(self))
        self.log('Plugins are loaded')

    def update(self):
        self.__init_apps()
        self.__listener.apps = self.apps

    def __init_apps(self):
        class App:
            def __init__(self, name, port, cmds, prefixes, folder, is_enabled, launch_time):
                self.name = name
                self.port = port
                self.cmds = cmds
                self.prefixes = prefixes
                self.folder = folder
                self.is_enabled = is_enabled
                self.is_port_busy = True
                self.last_act = 0
                self.last_check = 0
                self.launch_time = launch_time
                self.check_state = 0
        apps = []
        path_shit = './../apps/'
        dirs = os.listdir(path_shit)
        for dirr in dirs:
            config_path = path_shit+dirr+'/config'
            if not os.path.exists(config_path):
                continue
            try:
                with open(config_path, 'r', encoding='utf-8') as file:
                    s1 = file.readline()
                    assert(s1.startswith('port=')), 'Config file is uncorrect (port)'
                    port = int(s1[5:-1])
                    s2 = file.readline()
                    assert(s2.startswith('commands=')), 'Config file is uncorrect (commands)'
                    cmds_str = s2[9:-1]
                    cmds_dict = ast.literal_eval(cmds_str)
                    s3 = file.readline()
                    assert(s3.startswith('prefixes=')), 'Config file is uncorrect (prefixes)'
                    prefixes_str = s3[9:-1]
                    prefixes_dict = ast.literal_eval(prefixes_str)
                    s4 = file.readline()
                    assert(s4.startswith('name=')), 'Config file is uncorrect (name)'
                    name = s4[5:-1]
                    s5 = file.readline()
                    assert(s5.startswith('launch_time=')), 'Config file is uncorrect (launch_time)'
                    launch_time = float(s5[12:-1])
                    one_app = App(name, port, cmds_dict, prefixes_dict, dirr, False, launch_time)
                    apps.append(one_app)
                self.log(f'Loaded app "{name}" with port {port}')

            except Exception as e:
                self.log(f'!!ERROR!!\nAttempt to load app is unsuccessfully:\n{str(type(e))}\n{str(e)}')
        self.apps = apps

        for app in apps:
            self.check_connection(app)

    def send_to_port(self, msg, app, timeout=1, max_ans_size=1024):
        app.is_port_busy = True
        sock = self.sock
        while not self.__is_listen_port_listening: pass
        self.__go_on_sleep = True
        sock.sendto(b'stop', ('localhost', self.BOT_PORT))
        while not self.__is_listen_port_sleeping: pass
        sock.settimeout(timeout)
        self.log(f'"{msg}" sending to app"{app.name}":{app.port}')
        sock.sendto(msg.encode('utf-8'), ('localhost', app.port))
        try:
            ans, addr = sock.recvfrom(max_ans_size)
            self.__go_on_sleep = False
            app.is_port_busy = False
            ans = ans.decode('utf-8')
            if addr[1] != app.port:
                shit = app.name
                self.log(f'Answer came from {shit}: {ans}')
                self.sender.report('Произошла коллизия. Ожидался запрос от одного порта, получился другой')
                return None
            self.log(f'App "{app.name}":{app.port} responded: {ans}')
            return ans
        except (ConnectionResetError, socket.timeout) as e:
            self.__go_on_sleep = False
            self.log(f'App "{app.name}":{app.port} doesn\'t respond')
            app.is_enabled = False
            return None

    def __update_states(self):
        for app in self.apps:
            lnc = time.time() - app.launch_time
            cha = time.time() - app.last_act
            if lnc < 5.0*60.0 or cha < 1.0*60.0:
                app.check_state = 1
            elif lnc < 1.0*60.0*60.0 or cha < 5.0*60.0:
                app.check_state = 2
            elif lnc < 4.0*60.0*60.0 or cha < 20.0*60.0:
                app.check_state = 3
            elif lnc < 24.0*60.0*60.0 or cha < 60.0*60.0:
                app.check_state = 4
            elif lnc > 24.0*60.0*60.0:
                app.check_state = 5

    def __collect_check_list(self):
        for i in range(len(self.apps)):
            app = self.apps[i]
            if app.is_enabled == False or app.is_port_busy:
                continue
            if app.check_state == 1:
                yield i
            elif app.check_state == 2 and time.time() - app.last_check > 60.0:
                yield i
            elif app.check_state == 3 and time.time() - app.last_check > 5.0*60.0:
                yield i
            elif app.check_state == 4 and time.time() - app.last_check > 30.0*60.0:
                yield i
            elif app.check_state == 5 and time.time() - app.last_check > 60.0*60.0:
                yield i

    def monitor_apps(self):
        time.sleep(10)
        try:
            while True:
                self.__update_states()
                check_list = list(self.__collect_check_list())
                if len(check_list) == 0:
                    time.sleep(11)
                    continue
                for i in check_list:
                    app = self.apps[i]
                    if app.is_enabled == True and not app.is_port_busy and time.time() - self.last_msg > 3.0:
                        app.last_check = time.time()
                        ans = self.send_to_port('is_all_right', app, 0.6, 8)
                        if ans == None:
                            self.sender.report(f'Приложение {app.name} внезапно перестало отвечать')
                            self.log(f'!!ERROR!!\nApp {app.name} suddenly stopped responding')
                            app.is_enabled = False
                        elif ans == '1':
                            self.sender.report(f'Процесс приложения {app.name} неожиданно завершил работу')
                            self.log(f'!!ERROR!!\nThread of app {app.name} crashed')
                        elif ans != '2' and ans != '0':
                            self.sender.report('Неожиданный ответ в функции BotBase.monitor_apps. Посмотри логи')
                            self.log(f'!!ERROR!!\nIt\'s strange answer: "{ans}"')
                    time.sleep(11.0/len(check_list))
        except Exception as e:
            self.log('!! ERROR !!\nException in the monitor_apps. It stopped\n'+str(type(e))+'\n'+str(e))
            self.sender.report('!! ERROR !!\nException in the monitor_apps. It stopped\n'+str(type(e))+'\n'+str(e))
            return

    def check_connection(self, app):
            if self.send_to_port('ping', app, 0.1, 32) == 'pong':
                self.log(f'App "{app.name}":{app.port} responded Pong')
                app.is_enabled = True
                return True
            else:
                if app.is_enabled == True:
                    self.log(f'App "{app.name}":{app.port} is disabled')
                    app.is_enabled = False
                return False

    def _start_(self, mode=0):
        if mode == 0:
            pass #quiet start
        elif mode == 1:
            self.sender.report('Бот запущен!')
            self.log('Bot is started. mode %d' % mode) 
        elif mode == 2:
            self.sender.report('Бот перезапущен!')
            self.log('Bot is restarted %d' % mode) 
        elif mode == 3:
            self.log('Bot is restarted %d' % mode)
        
        self.__listen__()

    def __listen__(self):
        try:
            self.__listener.listen()
        except requests.exceptions.ConnectionError:
            self.log('Connection ERROR in botbase')
            time.sleep(60)
            self._start_(3)

        except requests.exceptions.ReadTimeout:
            self.log('ReadTimeout (night reboot)')
            time.sleep(60)
            self._start_(3) 
        
        except Exception as e:
            self.sender.report('Exception in Botbase:\n'+str(type(e))+'\n'+str(e))
            self.sender.report('Бот запустится через 60 секунд...')
            self.log('!!ERROR!!\nException in Botbase:\n'+str(type(e))+'\n'+str(e))
            self.log('Bot is pausing about 60 seconds')
            time.sleep(60)
            self._start_(1)
