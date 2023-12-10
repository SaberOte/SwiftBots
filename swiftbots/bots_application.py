import asyncio
from typing import Type, Optional
from enum import Enum

from swiftbots.loggers import SysIOLogger
from swiftbots.types import IMessageHandler, IController, ILogger, IView
from swiftbots.bots import Bot, _instantiate_in_bots
from swiftbots.message_handlers import MultiControllerMessageHandler
from swiftbots.listeners import listen_asynchronously


class RunnerMode(Enum):
    ASYNCHRONOUS = 1
    SYNCHRONOUS = 2
    MULTITHREADING = 3
    CUSTOM = 4


class BotsApplication:

    __logger: ILogger = None
    __bots: list[Bot] = []

    def use_logger(self, logger: ILogger) -> None:
        """
        Set logger instance
        """
        assert isinstance(logger, ILogger), 'Logger must be of type ILogger'
        self.__logger = logger

    def use_message_handler(self, message_handler: IMessageHandler) -> None:
        """
        Message handler configures rules forwarding messages
        to appropriate controller and executes appropriate method
        """
        assert isinstance(message_handler, IMessageHandler), 'Message handler must be of type IMessageHandler'
        self.__message_handler = message_handler

    def add_bot(self, view_type: type[IView], controller_types: list[type[IController]], message_handler_type: type[IMessageHandler] = None) -> None:
        """
        Adds a bot with one view and some bound controllers.
        """
        assert type(view_type) is Type, 'view_type must be class, not object'
        assert issubclass(view_type, IView), 'view must be of type IView'
        assert len(controller_types) > 0, 'No controllers'
        assert message_handler_type is None or issubclass(message_handler_type, IMessageHandler)
        for controller_type in controller_types:
            assert type(controller_type) is Type, 'controller_types must be classes, not objects'
            assert issubclass(controller_type, IController), 'Controllers must be of type IController'

        if message_handler_type is None:
            message_handler_type = MultiControllerMessageHandler
        self.__bots.append(Bot(view_type, controller_types, message_handler_type, self.__logger))

    def run(self, mode: RunnerMode = RunnerMode.ASYNCHRONOUS) -> None:
        """
        Start application to listen all the bots in asynchronous event loop
        """
        assert isinstance(mode, RunnerMode)

        if self.__logger is None:
            self.use_logger(SysIOLogger())

        if len(self.__bots) == 0:
            self.__logger.critical('No bots used')
            return
        if len(self.__bots) > 1:
            # TODO: test more than 1 bot
            self.__logger.critical("Didn't test more than 1 bot, so exit")
            return

        _instantiate_in_bots(self.__bots)

        if mode == RunnerMode.ASYNCHRONOUS:
            self.__run_async_listening()
        else:
            # TODO: make synchronous and multithread mode
            self.__logger.critical('Can be run only asynchronous mode yet')
            return

    def __run_async_listening(self) -> None:
        tasks: set[asyncio.Task] = set()

        for name in handlers:
            # handler waits any updates from outer resources
            task = asyncio.create_task(handlers[name]())
            task.set_name(name)
            tasks.add(task)
        while 1:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                name = task.get_name()
                try:
                    result = task.result()
                    print(f"Listener {name} was finished and restarted with result {result}", file=stderr)
                except:
                    print(f"Listener {name} was raised and restarted with exception:\n{format_exc()}", file=stderr)
                tasks.remove(task)
                new_task = asyncio.create_task(handlers[name]())
                new_task.set_name(name)
                tasks.add(new_task)

        asyncio.run(self.__start_listener())
