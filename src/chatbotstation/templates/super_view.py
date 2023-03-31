import os, threading, sys, inspect
from .. import logger
from ..communicators import Communicator
from ..config import read_config, write_config
from abc import ABC, abstractmethod
from .super_plugin import SuperPlugin
from typing import Optional, Callable
'''
что вьюшка должна уметь делать?
- слушать и передавать всю инфу о сообщении ядру
- включаться, как процесс
- выключаться, как процесс
'''


class SuperView(ABC):
    plugins: list[str] = []  # "подписка" на плагины. Каждое вьюшке соответствуют какие-то плагины. Команда будет искаться в них
    any: Optional[SuperPlugin] = None  # если ни один плагин не подошёл, будет вызван плагин, который записан в any
    inner_commands: {str: str} = {}  # команды от ядра бота конкретно для этой вьюшки
    name: str
    log: Callable[[str], None]
    authentic_style = False
    error_message = 'Error occurred'
    unknown_error_message = 'Unknown command'
    refuse_message = 'Access forbidden'

    def init(self, flags: list[str]):
        self.name = self.__module__.split('.')[-1]
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

    def report(self, message):  # Будет отсылаться администратору важные сообщения
        if self.authentic_style:
            self.send(message, self.admin)
            self.log(f'Reported "{message}"')
            return
        raise NotImplementedError('Not implemented method report in ' + self.name)

    def error(self, message, context):  # Сообщить пользователю, что произошла внутренняя ошибка. Дублируется админу
        if self.authentic_style:
            if context.sender != self.admin:
                self.reply(self.error_message, context)
            self.report(str(message))
            self.log('ERROR\n' + str(message))
            return
        raise NotImplementedError('Not implemented method error in ' + self.name)

    def reply(self, message, context):  # Ответить тому же пользователю, который прислал сообщение
        if self.authentic_style:
            assert 'sender' in context, 'Authentic style needs "sender" defined in context!'
            self.send(message, context['sender'])
            self.log(f'''Replied "{message}" to "{context['sender']}"''')
            return
        raise NotImplementedError('Not implemented method reply in ' + self.name)

    def unknown_command(self, context):  # Если пользователь прислал непонятно чо, ему нужно об этом сказать
        if self.authentic_style:
            self.reply(self.unknown_error_message, context)
            self.log('Unknown command')
            return
        raise NotImplementedError('Not implemented method unknown_command in ' + self.name)

    def refuse(self, context):  # Если пользователю нельзя использовать это, то вежливо отказать
        if self.authentic_style:
            self.reply(self.refuse_message, context)
            self.log('Forbidden')
            return
        raise NotImplementedError('Not implemented method refuse in ' + self.name)

    # Дальше методы для внутреннего пользования
    def enable_in_config(self):
        config = read_config()
        if self.name in config['Disabled_Views']:
            del config['Disabled_Views'][self.name]
            write_config(config)

    def init_listen(self):  # listens the outer resource
        self.core_listener.start()
        self.enable_in_config()
        while 1:
            try:
                for data in self.listen():  # calls overridden listen()
                    assert isinstance(data, dict), 'View yields something not DICT'
                    self.comm.send(f"mes|{str(data)}", 'core')
            except Exception as e:
                msg = 'EXCEPTION ' + str(e)
                self.comm.send(msg, 'core')
                self.log(msg)
                self.report('Exception in listen: ' + msg)

    def listen_port(self):  # waits commands from core bot
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
                            self.comm.send('unknown command', data['view_sender'], data['session_id'])
                    else:
                        command = message
                        if command == 'exit':
                            self.log('View is exited')
                            config = read_config()
                            config["Disabled_Views"][self.name] = ''
                            write_config(config)
                            self.comm.send('exited', data['view_sender'], data['session_id'])
                            self.comm.close()
                            os._exit(1)
                        elif command == 'ping':
                            self.comm.send('pong', data['view_sender'], data['session_id'])
                        else:
                            self.comm.send('unknown command', data['view_sender'], data['session_id'])
            except Exception as e:
                try:
                    msg = 'EXCEPTION ' + str(e)
                    self.comm.send(msg, 'core')
                    self.log(msg)
                finally:
                    try:
                        self.report('This is super_view error: ' + str(e))
                        # self.comm.close()
                        # self.report('THIS view dies with ' + msg)
                    except:
                        os._exit(1)
