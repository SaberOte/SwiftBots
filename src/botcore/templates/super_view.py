import os, threading, sys, inspect, time
from signal import SIGKILL, SIGUSR1
from traceback import format_exc
from .. import logger
from ..communicators import Communicator
from ..config import read_config, write_config
from abc import ABC, abstractmethod
from typing import Callable
'''
что вьюшка должна уметь делать?
- слушать и передавать всю инфу о сообщении ядру
- включаться, как процесс
- выключаться, как процесс
'''


class SuperView(ABC):
    controllers: list[str] = []  # "подписка" на плагины. Каждое вьюшке соответствуют какие-то плагины. Команда будет искаться в них
    inner_commands: {str: str} = {}  # команды от ядра бота конкретно для этой вьюшки
    name: str
    log: Callable[[str], None]
    authentic_style = False
    error_message = 'Error occurred'
    unknown_error_message = 'Unknown command'
    refuse_message = 'Access forbidden'
    exit_message = 'View exited.'

    def init(self, flags: list[str]):
        """
        Preparing a view for execution or serving by core.
        Launches with its own communicator, logger and thread with port listening if that's 'launch' flag
        If it launchs not as process, it's only name property processing
        :param flags: flags describing is in the file __main__.py
        """
        self.name = self.__module__.split('.')[-1]
        self._flags = flags
        if self.authentic_style:
            assert 'send' in dir(self), 'Authentic style needs to exist "send" method!'
            assert len(inspect.getfullargspec(self.send)[0]) == 3, \
                'Authentic style needs method "send" to have 3 parameters'
            assert 'admin' in dir(self), 'Authentic style needs to exist "admin" property'
        if 'launch' in flags:
            self.log = logger.Logger(self.name, 'debug' in flags).log
            self.comm = Communicator(self.name, self.log)
            self.core_listener = threading.Thread(target=self.listen_port, daemon=True)

    @abstractmethod
    def listen(self):  # Должен быть определён. Чтобы слушать внешний источник команд
        raise NotImplementedError('Not implemented method listen in ' + self.name)

    def report(self, message: str):
        """
        Send important message to admin
        :param message: report message
        :return: any
        """
        if self.authentic_style:
            self.log(f'Reported "{message}"')
            return self.send(message, self.admin)
        raise NotImplementedError('Not implemented method report in ' + self.name)

    def error(self, message: str, context: dict):
        """
        Inform user it is internal error. Admin's notifying too
        :param message: message is only for admin. User's looking at default message
        :param context: needs to have 'sender' property
        :return: any
        """
        if self.authentic_style:
            try:
                if context['sender'] != self.admin:
                    self.reply(self.error_message, context)
                    self.log('ERROR\n' + str(message))
            finally:
                return self.report(str(message))
        raise NotImplementedError('Not implemented method error in ' + self.name)

    def reply(self, message: str, context: dict):
        """
        Reply the sender
        :param message: reply message
        :param context: needs to have 'sender' property
        :return: any
        """
        if self.authentic_style:
            assert 'sender' in context, 'Authentic style needs "sender" defined in context!'
            self.log(f'''Replied "{context['sender']}":\n"{message}"''')
            return self.send(message, context['sender'])
        raise NotImplementedError('Not implemented method reply in ' + self.name)

    def unknown_command(self, context: dict):
        """
        If user sends some unknown shit, then say him about it
        :param context: needs to have 'sender' property
        """
        if self.authentic_style:
            self.log('Unknown command')
            return self.reply(self.unknown_error_message, context)
        raise NotImplementedError('Not implemented method unknown_command in ' + self.name)

    def refuse(self, context: dict):
        """
        If user can't use it, then he must be aware
        :param context: needs to have 'sender' property
        """
        if self.authentic_style:
            self.log('Forbidden')
            return self.reply(self.refuse_message, context)
        raise NotImplementedError('Not implemented method refuse in ' + self.name)

    # Further methods for inner purposes
    def enable_in_config(self):
        config = read_config('config.ini')
        if self.name in config['Disabled_Views']:
            del config['Disabled_Views'][self.name]
            write_config(config, 'config.ini')

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
                self.report(msg)
                # prevent 1 billion looped error tracebacks per second
                error_count += 1
                elapsed_time = time.time() - last_error_time
                last_error_time = time.time()
                if elapsed_time > 60:
                    error_count = 1  # reset counter because previous error was long ago
                elif error_count > 5:
                    self.report('Error rate is too high. Waiting for one minute...')
                    time.sleep(60)
                    error_count = 0

    def listen_port(self):
        """Waits commands from core bot. Executing in another thread"""
        self.log('start listening')
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
                try:
                    msg = 'EXCEPTION ' + format_exc()
                    self.report(msg)
                finally:
                    try:
                        self.log('This view is gonna die right after this message\n' + format_exc())
                    except:
                        os.kill(os.getpid(), SIGKILL)
