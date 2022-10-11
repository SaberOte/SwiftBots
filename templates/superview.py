import os, threading, logger, sys
from communicator import Communicator
from config import readconfig, writeconfig
from abc import ABC, abstractmethod
'''
что вьюшка должна уметь делать?
- слушать и передавать всю инфу о сообщении ядру
- включаться, как процесс
- выключаться, как процесс
'''


class SuperView(ABC):
    plugins = []  # "подписка" на плагины. Каждое вьюшке соответствуют какие-то плагины. Команда будет искаться в них
    any = None  # если ни один плагин не подошёл, будет вызван плагин, который записан в any
    inner_commands = []  # команды от ядра бота конкретно для этой вьюшки

    def __init__(self, is_daemon=True):
        if is_daemon:
            self.view_name = type(self).__name__.lower()
            self.log = logger.Logger('-d' in sys.argv, './logs/').log
            self.comm = Communicator(self.view_name, self.log)
            self.core_listener = threading.Thread(target=self.listen_port, daemon=True)
            self.core_listener.start()
            self.enable_in_config()
        else:
            self.view_name = type(self).__name__.lower()
            self.log = logger.Logger('-d' in sys.argv, '../logs/').log

    @abstractmethod
    def listen(self):  # должен быть определён. Чтобы слушать внешний источник команд
        raise NotImplementedError('Not implemented method listen in ' + self.view_name)

    @abstractmethod
    def report(self, message):  # должен быть определён. Будет отсылаться администратору важные сообщения
        raise NotImplementedError('Not implemented method report in ' + self.view_name)

    def error(self):  # сообщить пользователю, что произошла внутренняя ошибка. Необязательно
        pass

    def reply(self, message):  # ответить тому же пользователю, который прислал сообщение
        raise NotImplementedError('Not implemented method reply in ' + self.view_name)

    def unknown_command(self):  # если пользователь прислал непонятно чо, ему нужно об этом сказать
        pass
        # raise NotImplementedError('Not implemented method unknown_command in ' + self.view_name)

    def refuse(self):  # если пользователю нельзя использовать это, то вежливо отказать
        pass
        # raise NotImplementedError('Not implemented method refuse in ' + self.view_name)

    # дальше методы для внутреннего пользования
    def enable_in_config(self):
        config = readconfig()
        if self.view_name in config['Disabled_Views']:
            del config['Disabled_Views'][self.view_name]
            writeconfig(config)

    def init_listen(self):  # listens the outer resource
        while 1:
            try:
                for data in self.listen():  # calls overridden listen()
                    if isinstance(data, dict) and 'command' in data:
                        self.comm.send(f"com|{data['command']}|{str(data)}", 'core')
                    else:
                        self.comm.send('any|'+str(data), 'core')
            except Exception as e:
                msg = 'EXCEPTION ' + str(e)
                self.comm.send(msg, 'core')
                self.log(msg)
                self.report('It is impossible error in superview.py with exception: ' + msg)

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
                            self.comm.send('unknown command', data['sender'], data['session_id'])
                    else:
                        command = message
                        if command == 'exit':
                            self.log('View is exited')
                            config = readconfig()
                            config["Disabled_Views"][self.view_name] = ''
                            writeconfig(config)
                            self.comm.send('exited', data['sender'], data['session_id'])
                            self.comm.close()
                            os._exit(1)
                        elif command == 'ping':
                            self.comm.send('pong', data['sender'], data['session_id'])
                        else:
                            self.comm.send('unknown command', data['sender'], data['session_id'])
            except Exception as e:
                msg = 'EXCEPTION ' + str(e)
                self.comm.send(msg, 'core')
                self.log(msg)
                self.comm.close()
                self.report('THIS view dies with ' + msg)
                os._exit(1)
