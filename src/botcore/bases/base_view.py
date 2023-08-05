import os, threading, inspect, time
from signal import SIGKILL, SIGUSR1
from traceback import format_exc
from abc import ABC, abstractmethod
from src.botcore.communicators import Communicator
from src.botcore.config import read_config, write_config


class BaseView(ABC):
    name: str

    def init(self):
        """
        Preparing a view for execution or serving by core.
        Launches with its own communicator and thread with port listening if that's 'launch' flag
        If it launches not as process, it's only name property processing
        """
        self.name = self.__module__.split('.')[-1]

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
            print("Couldn't report because of:", e)
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
                print(msg)
                reported = self.try_report(msg)
                if reported != 1:
                    print('Not reported', reported)
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
