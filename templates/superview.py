import os, sys, threading
from communicator import Communicator
from inspect import getsourcefile
from abc import ABC, abstractmethod, abstractproperty
'''
что вьюшка должна уметь делать?
- слушать и передавать всю инфу о сообщении ядру
- включаться, как процесс
- выключаться, как процесс
'''
'''Закончил здесь. Нужно треадинг сделать и ответ на exit и ping pong'''


class SuperView(ABC):
    def __init__(self):
        self.comm = Communicator('../../resources/config.ini', type(self).__name__.lower()+'_sender')
        self.bot_listener = threading.Thread(target=)

    @abstractmethod
    def listen(self):
        raise Exception('Not implemented method')

    def init_listen(self):  # listens the outer resource
        for command in self.listen():  # calls overridden listen()
            self.comm.send(command, 'core')

    def listen_port(self):  # waits commands from core bot
        comm = Communicator('../../resources/config.ini', type(self).__name__.lower()+'_portlistener')
        for command in comm.listen():
            if command['message'] == 'exit':

