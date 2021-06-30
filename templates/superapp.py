import random, socket, os, sys, time, inspect, subprocess, ast, re, threading
from sys import platform
from keys import KeyManager
from msgsender import Sender
from superplugin import SuperPlugin, admin_only, superadmin_only
from apimanager import ApiManager
from logger import Logger

class SuperApp(SuperPlugin):
    is_active = False
    user_id = ''
    message = ''
    prefixes = {}
    cmds = {}
    def __init__(self):
        is_debug = False
        for arg in sys.argv:
            if arg == '-d':
                is_debug = True
        with open("config", 'r', encoding='utf-8') as config:
            self.name = config.read().split('\n')[3][5:]
            if len(self.name) == 0:
                raise Exception('name is zero word')
        logger = Logger(is_debug, './logs/')
        self.log = logger.log
        try: os.remove('ERROR.txt')
        except: pass
        shits = list(self.base_cmds.keys())
        for shit in shits:
            self.cmds[f"{self.name} {shit}"] = self.base_cmds[shit]

        self.log(f'App {self.name} is launching')
        self.keys = KeyManager('./../../resources/data.json', logger.log)
        self.api = ApiManager(self.keys, logger.log)
        self.sender = Sender('./../../resources/', self.keys, self.api, logger.log)
        self.log('Base services are loaded')
        self.user_id = self.keys.admin_id

        BOT_PORT = self.keys.bot_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bot_port = BOT_PORT
        while True:
            counter = 0
            try:
                counter += 1
                app_port = random.randint(5000, 5999)
                self.sock.bind(('127.0.0.1', app_port))
                break
            except OSError:
                if counter > 1000:
                    self.log('!!ERROR!!\nMore than 1000 attempts to bind socket have been missed')
                    os._exit(1)

        self.app_port = app_port
        self.log(f'Binded {str(self.name)} with port = {app_port}')
        with open('config', 'w', encoding='utf-8') as config:
            config.write(
f"""port={self.app_port}
commands={str({key:self.cmds[key].__name__ for key in self.cmds})}
prefixes={str({key:self.prefixes[key].__name__ for key in self.prefixes})}
name={self.name}
launch_time={time.time()}
date={time.ctime()}""")
        
        self.thread = None


    def listen(self):
        #skip stuff
        self.sock.settimeout(0.1)
        while True:
            try:
                self.sock.recv(8192)
            except: break

        #check link with bot
        self.log('"ping" sending to bot')
        self.sock.settimeout(2)
        self.sock.sendto(b'ping', ('127.0.0.1', self.bot_port))
        try:
            respond = self.sock.recv(64)
        except ConnectionResetError:
            #self.sender.report(f"No opened host with {self.bot_port} port")
            self.log(f"!!ERROR!!\nNo opened host with {self.bot_port} port")
            return
        except socket.timeout:
            #self.sender.report("It's no respond from bot!")
            self.log("!!ERROR!!\nIt's no respond from bot!")
            return
        if respond != b'pong':
            #self.sender.report('Uncorrect respond from bot!')
            self.log('!!ERROR!!\nUncorrect respond from bot!')
            return
        self.log('Pong!')

        # listening
        self.sender.report(f'Приложение "{self.name}" запущено!')
        self.log('Listening...')
        self.log('"update" sending to the bot')
        self.sock.sendto(b'update', ('localhost', self.bot_port))
        self.sock.settimeout(60*60*4)
        while True:
            msg = ''
            try:
                msg, addr = self.sock.recvfrom(4096)
                if len(msg) == 4096:
                    self.sock.settimeout(0.1)
                    while True:
                        try:
                            msg_cr = self.sock.recv(16384)
                            msg += msg_cr
                        except socket.timeout: 
                            self.sock.settimeout(60*60*4)
                            break
            except socket.timeout: continue
            msg = msg.decode('utf-8')
            self.log(f'Socket received message: "{msg}"')
            if re.match(r"{'user_id':'\d+','message':'.*','function':'.*'}$", msg):
                threading.Thread(target=self.handler, args=(msg,)).start()
            elif msg == 'ping' and addr[1] == self.bot_port:
                self.log('"pong" sending to the bot')
                self.sock.sendto(b'pong', ('localhost', self.bot_port))
            elif msg == 'get_info' and addr[1] == self.bot_port:
                ans = self.get_info()
                self.log(f'Answered(1): {ans}')
                self.sock.sendto(ans.encode('utf-8'), ('localhost', self.bot_port))
            elif msg == 'is_running' and addr[1] == self.bot_port:
                ans = str(self.is_running())
                self.log(f'Answered(2): {ans}')
                self.sock.sendto(ans.encode('utf-8'), ('localhost', self.bot_port))
            elif msg == 'is_all_right':
                ans = self.is_all_right()
                self.log(f'Answered(3): {ans}')
                self.sock.sendto(ans.encode('utf-8'), ('localhost', self.bot_port))
            else:
                self.sender.error(self.user_id, f'В сокет приложения "{self.name}" пришло сообщение неправильного формата: {msg}')

    def handler(self, msg):
        # формат msg r"{'user_id':'\d+','message':'.*','function':'.*'}$"
        #пример {'user_id':'179995182','message':'ping','function':'send_pong'} 
        try:
            js = ast.literal_eval(msg)
        except Exception as e:
            self.log(f'!!ERROR!!\nException in "SuperApp.handler":\n{type(e)}\n{str(e)}')
            self.sender.report(f'Exception in "SuperApp.handler":\n{type(e)}\n{str(e)}')
            return

        user_id = js.get('user_id')
        message = js.get('message')
        self.user_id = user_id
        self.message = message
        function_name = js.get('function')
        self.log(f'Received message from "{user_id}": "{message}"')

        function = None
        methods = inspect.getmembers(self, inspect.ismethod)
        for method in methods:
            if method[0] == function_name:
                function = method[1]
        if function == None:
            self.log(f'!!ERROR!!\nThere is no function with such name "{function_name}"')
            self.sender.error(user_id, f'В классе "{self.name}" нет метода "{function_name}"')
            return

        try:
            function()
        except Exception as e:
            self.sender.error(user_id, f'Exception in app "{self.name}" in method "{function_name}":\n{type(e)}\n{str(e)}')
            self.log(f'!!ERROR!!\nException in app "{self.name}" in method "{function_name}":\n{type(e)}\n{str(e)}')

    def launch(self):
        pass
    
    @admin_only
    def _radical_stop(self):
        pass

    @admin_only
    def _stop(self):
        self.is_active = False
        if self.thread == None:
            self.sender.error(self.user_id, f'Поток приложения "{self.name}" не был запущен')
            return
        self.log('There is query to stop the thread')
        t = time.time()
        while time.time() - t < 10:
            if not self.thread.is_alive():
                self.sender.error(self.user_id, f'Поток приложения "{self.name}" остановлен')
                self.log('The thread has stopped by stop()')
                return
        self.sender.error(self.user_id, f'Поток приложения "{self.name}" не удаётся остановить более 10 секунд. Можно подождать или завершить его насильно')

        def fuck():
            while self.__superbitch__:
                if self.thread.is_alive() == False:
                    self.log('The thread is stopped')
                    self.sender.error(self.user_id, f'Поток приложения "{self.name} остановлен')
        threading.Thread(target=fuck, daemon=True).start()

    @admin_only
    def _launch(self):
        try:
            if self.thread == None or not self.thread.is_alive():
                def func_wrapper():
                    try:   
                        self.launch()
                        self.is_active = False
                    except Exception as e:
                        self.sender.report(f'Исключение в "{self.name}" в мультипоточной функции:\n{str(type(e))}\n{str(e)}')
                        self.log(f'!!ERROR!!\nException in app "{self.name}" in the multithread function:\n{str(type(e))}\n{str(e)}')
                self.thread = threading.Thread(target=func_wrapper, daemon=True)
                self.log('Created thread object')
                self.is_active = True
                self.sender.error(self.user_id, f'Поток приложения "{self.name}" запускается')
                self.thread.start()
                self.log('Thread is ran')
            elif self.thread.is_alive():
                self.sender.error(self.user_id, f'Служба класса "{self.name}" итак активна. Можете её остановить')
        except Exception as e:
            self.sender.report("Exception in SuperApp._launch:\n"+str(type(e))+'\n'+str(e))

    __superbitch__ = True
    @admin_only
    def _exit(self):
        self.soft_exit()
        user_id = self.user_id
        self.is_active = False
        if self.thread and self.thread.is_alive():
            self.sender.error(self.user_id, f'Поток приложения "{self.name}" останавливается...')
        else:
            self.sender.error(self.user_id, f'Приложение "{self.name}" закрыто')
            self.log('Program suspended')
            self.sock.sendto(b'exited', ('localhost', self.bot_port))
            self.sock.close()
            os._exit(0)
        self.log('App is suspending')
        t = time.time()
        while t - time.time() < 65:
            if self.thread.is_alive() == False:
                self.log('The thread is stopped')
                self.sender.error(self.user_id, f'Поток остановлен. Приложение "{self.name}" закрыто.')
                self.sock.sendto(b'exited', ('localhost', self.bot_port))
                self.sock.close()
                self.log('Program suspended')
                os._exit(0) 
        if self.thread.is_alive() == True:
            self.sender.error(user_id, 'Поток не получается остановить больше минуты. Можно подождать дольше или завершить приложение насильно')

        def fuck():
            while self.__superbitch__:
                if self.thread.is_alive() == False:
                    self.log('The thread is stopped')
                    self.sender.error(self.user_id, f'Поток остановлен. Приложение "{self.name}" закрыто.')
                    self.sock.sendto(b'exited', ('localhost', self.bot_port))
                    self.sock.close()
                    self.log('Program suspended')
                    os._exit(0)
        threading.Thread(target=fuck, daemon=True).start()

    def soft_exit(self):
        pass

    @admin_only
    def _radical_exit(self):
        user_id = self.user_id
        self.is_active = False
        self.log('App force suspends')
        self.sender.error(user_id, f'Приложение "{self.name}" насильно закрыто.')
        self.sock.sendto(b'exited', ('localhost', self.bot_port))
        self.sock.close()
        self.log('Program force suspended')
        os._exit(0)

    def __up_new_app(self):
        self.log('Program is booting')
        fullpath = os.getcwd()
        if platform == 'linux':
            fold = fullpath.split('/')[-1]
            bot_name = fullpath.split('/')[-3]
        elif platform == 'win32':
            fold = fullpath.split('\\')[-1]
        else:
            self.log('!!ERROR!!\nYour system is not supported. Is it reboot??? Are you fucking ??')
            return
        path = fullpath[:-(len(fold)+1)]
        os.chdir(path)
        if platform == 'linux':
            subprocess.Popen(['python3',fold,'{%s}'%bot_name])
        else:
            subprocess.Popen('python %s' % fold)
    
    @admin_only
    def _reboot(self):
        self.soft_exit()
        user_id = self.user_id
        self.is_active = False 
        if self.thread and self.thread.is_alive(): 
            self.sender.error(user_id, f'Поток приложения "{self.name}" останавливается...')
        self.log('App is rebooting')
        if self.thread == None or not self.thread.is_alive():
            self.sender.error(user_id, f'Приложение "{self.name}" закрыто.')
            self.__up_new_app()
            self.sock.close()
            self.log('Program suspended')
            os._exit(0)
        t = time.time()
        while time.time() - t < 65:
            if self.thread.is_alive() == False:
                self.log('The thread is stopped')
                self.sender.error(user_id, f'Поток остановлен. Приложение "{self.name}" закрыто.')
                self.__up_new_app()
                self.sock.close()
                self.log('Program suspended')
                os._exit(0)
                 
        if self.thread.is_alive() == True:
            self.sender.error(user_id, 'Поток не получается остановить больше минуты. Можно подождать дольше или завершить приложение насильно')
        def __fuck():
            while self.__superbitch__:
                if self.thread.is_alive() == False:
                    self.log('The thread is stopped')
                    self.sender.error(user_id, f'Поток остановлен. Приложение "{self.name}" закрыто.')
                    self.__up_new_app()
                    self.sock.close()
                    self.log('Program suspended')
                    os._exit(0)
        threading.Thread(target=__fuck, daemon=True).start()

    @admin_only
    def _radical_reboot(self):
        self.sender.error(self.user_id, f'Приложение "{self.name}" закрыто.')
        self.log('Radical reboot is called')
        self.__up_new_app()
        self.sock.close()
        self.log('Program force suspended')
        os._exit(0)

    def is_all_right(self):
        if self.thread != None and self.is_active:
            if self.thread.is_alive() == True:
                return '2'
            else:
                self.is_active = False
                return '1'
        return '0'

    def sleep(self, delay):
        counter = 0.0
        while counter < delay:
            time.sleep(0.5)
            counter += 0.5
            if self.is_active == False:
                sys.exit(0)

    def is_running(self):
        if self.thread == None:
            return False
        return self.thread.is_alive()

    def get_info(self):
        return ''

    base_cmds = {
            "stop" : _stop,
            "reboot" : _reboot,
            "ребут" : _reboot,
            "rreboot" : _radical_reboot,
            "rexit" : _radical_exit,
            "exit" : _exit,
            "выход" : _exit,
            "запустить" : _launch,
            "launch" : _launch,
            "start" : _launch,
            }
