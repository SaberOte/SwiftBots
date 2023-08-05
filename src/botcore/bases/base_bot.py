"""
BOT MUST:
1. Be launch in docker container single and standalone
2. Have at least 1 controller
3. May have views or tasks
4. If it has views, it pins views commands with controller methods
5. If it has tasks, each one has to have: task name, calling schedule, controller's method to call
"""
from abc import ABC, abstractmethod


class BaseBot(ABC):
    # "subscription" for controllers. Each view has some controllers to execute task or commands
    controllers: list[str] = []
    # commands not for user but for other views
    inner_commands: {str: str} = {}
    name: str

    def init(self):
        """
        Preparing a bot for execution.
        Launches with its own communicator and thread with port listening
        """
        self.name = self.__module__.split('.')[-1]
        '''if 'launch' in flags:  # FEATURE TEMPORARY DISABLED!!!!
            self.comm = Communicator(self.name)
            self.core_listener = threading.Thread(target=self.listen_port, daemon=True)'''

    def listen_port(self):
        """Waits commands from core bot. Executing in another thread"""
        print('start listening')
        last_error_time = 0
        error_count = 0
        while 1:
            try:
                for data in self.comm.listen():
                    print('Received ' + str(data))
                    message = data['message']
                    if message.startswith('com|'):  # есть команда и информация: формат com|КОМАНДА|НЕКАЯ_ИНФА
                        command = message[4:].split('|')[0]
                        data = message[5+len(command):]
                        if command in self.inner_commands:
                            self.inner_commands[command](self, data)
                        else:
                            self.comm.send('unknown command', data['sender_view'], data['session_id'])
                    else:
                        command = message
                        if command == 'exit':
                            print('View is exited')
                            config = read_config('config.ini')
                            config["Disabled_Views"][self.name] = ''
                            write_config(config, 'config.ini')
                            self.comm.send('exited', data['sender_view'], data['session_id'])
                            self.comm.close()
                            if self.authentic_style:
                                try:
                                    self.report(self.exit_message)
                                except: pass
                            os.kill(os.getpid(), SIGKILL)
                        elif command == 'ping':
                            self.comm.send('pong', data['sender_view'], data['session_id'])
                        elif command == 'update':
                            # Code execution transfers to __main__.py to the signal handler.
                            # This thread will be stacked
                            os.kill(os.getpid(), SIGUSR1)
                            self.comm.close()
                            return
                        else:
                            self.comm.send(f'unknown|{command}', 'core')
                            if data['sender_view'] != 'core':
                                self.comm.send(f'unknown|{command}', data['sender_view'], data['session_id'])
            except Exception as e:
                # prevent invisible looped errors
                self.try_report(format_exc())
                error_count += 1
                elapsed_time = time.time() - last_error_time
                last_error_time = time.time()
                if elapsed_time > 60:
                    error_count = 1  # reset counter because previous error was long ago
                elif error_count > 5:
                    reported = self.try_report('Error rate is too high. Waiting for one minute...')
                    if reported != 1:
                        print('This view is gonna die right after this message\n' + str(reported))
                        os.kill(os.getpid(), SIGKILL)
                    time.sleep(60)
                    error_count = 0
