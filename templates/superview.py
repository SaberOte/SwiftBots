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
    def __init__(self):
        self.view_name = type(self).__name__.lower()
        self.log = logger.Logger('-d' in sys.argv, './logs/').log
        self.comm = Communicator(self.view_name, self.log)
        self.core_listener = threading.Thread(target=self.listen_port, daemon=True)
        self.core_listener.start()
        self.enable_in_config()

    @abstractmethod
    def listen(self):
        raise Exception('Not implemented method')

    @abstractmethod
    def report(self):
        raise Exception('Not implemented method')

    def enable_in_config(self):
        config = readconfig()
        if self.view_name in config['Disabled_Views']:
            del config['Disabled_Views'][self.view_name]
            writeconfig(config)

    def init_listen(self):  # listens the outer resource
        for command in self.listen():  # calls overridden listen()
            self.comm.send(command, 'core')

    def listen_port(self):  # waits commands from core bot
        self.log('start listening')
        for data in self.comm.listen():
            self.log('Received ' + str(data))
            command = data['message']
            if command == 'exit':
                self.log('View is exited')
                config = readconfig()
                config["Disabled_Views"][self.view_name] = ''
                writeconfig(config)
                self.comm.send('exited', 'core', data['session_id'])
                self.comm.close()
                os._exit(1)
            elif command == 'ping':
                self.comm.send('pong', 'core', data['session_id'])
            else:
                self.comm.send('unknown command', 'core', data['session_id'])
