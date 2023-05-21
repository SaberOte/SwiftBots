import os, threading, inspect, time
from signal import SIGKILL, SIGUSR1
from traceback import format_exc
from abc import ABC, abstractmethod
from typing import Callable
from src.botcore import logger
from src.botcore.communicators import Communicator
from src.botcore.config import read_config, write_config


class BaseView(ABC):
    # "subscription" for controllers. Each view has got some controllers to execute task or commands
    controllers: list[str] = []
    # commands not for user but for other views
    inner_commands: {str: str} = {}
    name: str
    _flags: list[str]
    log: Callable

    def init(self, flags: list[str]):
        """
        Preparing a view for execution or serving by core.
        Launches with its own communicator, logger and thread with port listening if that's 'launch' flag
        If it launchs not as process, it's only name property processing
        :param flags: flags describing is in the file __main__.py
        """
        self.name = self.__module__.split('.')[-1]
        self._flags = flags
        if 'launch' in flags:
            self.log = logger.Logger(self.name, 'debug' in flags).log
            self.comm = Communicator(self.name, self.log)
            self.core_listener = threading.Thread(target=self.listen_port, daemon=True)

    @abstractmethod
    def listen(self):
        """
        Input pipe for commands from user.
        Method must use "yield" operator to give information and command
        """
        raise NotImplementedError(f'Not implemented method `listen` in {self.name}')

    def report(self, message: str):
        """
        Send important message to admin.
        Future is report broadcasts this message to views network or into master node of cluster
        :param message: report message
        """
        raise NotImplementedError('Not implemented method `report` in ' + self.name)

    # Further methods for inner purposes
    def enable_in_config(self):
        config = read_config('config.ini')
        if self.name in config['Disabled_Views']:
            del config['Disabled_Views'][self.name]
            write_config(config, 'config.ini')

    def try_report(self, msg):
        """
        Returns 1 if reported, Exception instance if not reported
        """
        try:
            self.report(msg)
            return 1
        except Exception as e:
            self.log("Couldn't report because of:", e)
            return e

    def init_listen(self):
        """
        Starts to listen own port and starts to listen outer resources with view.listen method.
        This method starts infinite loop and never returns anything
        """
        try:
            self.comm.send('started', 'core')
        except KeyError:
            pass  # core is not launched
        self.core_listener.start()
        self.enable_in_config()
        last_error_time = 0
        error_count = 0
        while 1:
            try:
                for data in self.listen():  # calls overridden listen()
                    assert isinstance(data, dict), 'View yields something not DICT'
                    self.comm.send(f"mes|{str(data)}", 'core')
            except Exception as e:
                msg = format_exc()
                self.log(msg)
                reported = self.try_report(msg)
                if reported != 1:
                    self.log('Not reported', reported)
                # prevent 1 billion looped error tracebacks per second
                error_count += 1
                elapsed_time = time.time() - last_error_time
                last_error_time = time.time()
                if elapsed_time > 60:
                    error_count = 1  # reset counter because previous error was long ago
                elif error_count > 5:
                    self.try_report('Error rate is too high. Waiting for one minute...')
                    time.sleep(60)
                    error_count = 0

    def listen_port(self):
        """Waits commands from core bot. Executing in another thread"""
        self.log('start listening')
        last_error_time = 0
        error_count = 0
        while 1:
            try:
                for data in self.comm.listen():
                    self.log('Received ' + str(data))
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
                            self.log('View is exited')
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
                        self.log('This view is gonna die right after this message\n' + str(reported))
                        os.kill(os.getpid(), SIGKILL)
                    time.sleep(60)
                    error_count = 0
