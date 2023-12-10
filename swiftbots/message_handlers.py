import re

from typing import Callable, Optional

from swiftbots.types import (IController, ILogger, IBasicView, IView,
                             IMessageHandler, MessageHandlingResult, IBasicMessageHandler,
                             IMultiControllerMessageHandler)


class CommandRepresentation:
    command_string: str
    method: Callable


class BasicMessageHandler(IBasicMessageHandler):
    """Handler just routing messages to `default` method of controller"""

    __controller: IController

    def __init__(self, controller: IController, logger: ILogger):
        logger.info('Initializing BasicMessageHandler')
        assert controller.default is not None, \
            'In basic message handler controller must have a `default` method'
        self.controller = controller

    async def handle_message_async(self, view: IView, context: dict) -> None:
        await self.__controller.default(view, context)


class MultiControllerMessageHandler(IMultiControllerMessageHandler):

    __controllers: list[IController]
    __commands: dict[str, Callable]
    __default_handler: Callable = None
    __logger: ILogger = None

    def __init__(self, controllers: list[IController], logger: ILogger):
        logger.info('Initializing ChatMessageHandler')
        self.__logger = logger
        self.__controllers = controllers

        self.__commands = dict()
        for controller in controllers:
            self.__commands.update(controller.cmds)
        logger.info(f'Initialized commands dict: {self.__commands}')

        self.__register_default_handler()
        self.__compile_regex_commands()

    def use_as_default(self, method: Optional[Callable]) -> None:
        """
        Define the method that will be called when no one
        commands was fitted to process the message.
        If it's needed to disable any default handler, may be passed None
        :param method: Function for defining the default command handler,
        or None to disable any default commands
        """
        self.__default_handler = method
        if method is not None:
            self.__logger.info(f'Registered default handler directly: {self.__default_handler}')
        else:
            self.__logger.info('Unregistered default handler directly')

    def handle_message_async(self, view: IBasicView, context: dict):
        """
        Receive the command and send it to one of controllers to execute.
        If no one fitted commands found, then send message to default handler.
        If it's no default handler, reject to execute command.
        :param view: View object
        :param context: dict, must contain at least 'message' field
        :return: MessageHandlingResult
        """
        message: str = context.message
        lower_message = message.lower()
        """
        # check exact match
        if lower_message in self.__commands:
            method = self.commands[lower_message]
            method(view=self.view, context=context)
            continue"""
        # check if the command has arguments like `ADDNOTE apple, cigarettes, cheese`, where `ADDNOTE` is command
        for name in self.compiled_commands_patterns:
            pattern: re.Pattern = self.compiled_commands_patterns[name]
            match = pattern.match(message)
            if match:
                message_without_command = match.group(2)
                context.message = message_without_command
                method = self.commands[name]
                method(view=self.view, context=context)
                continue
        # finally check `any`
        if self.any is not None:
            self.any(view=self.view, context=context)


    def __compile_regex_commands(self):
        """
        Compile with regex patterns all command names to faster search.
        Pattern is:
        1. Begins with NAME OF COMMAND (case-insensitive).
        2. Then any whitespace characters [ \f\n\r\t\v] (zero or more)
        3. Then any non-whitespace characters
        """
        for name in self.__commands:
            escaped_name = re.escape(name)
            pattern = re.compile(rf'^({escaped_name})\s*(\S*)$', re.IGNORECASE)
            self.__compiled_commands[name] = pattern


    def __register_default_handler(self):
        """
        Choose the default handler from all controllers.
        If that's only 1 `default` method found, it will be registered as default handler.
        If that's no `default` methods founds, default handler stays None and
        unfitted commands will be rejected to execute.
        If that's more than 1 `default` method found, first one will be registered.
        """
        defaults = filter(lambda c: c.default is not None, self.__controllers)
        if len(defaults) == 0:
            self.__logger.info('No default handlers in controllers')
        elif len(defaults) == 1:
            __default_handler = defaults[0]
            self.__logger.info(f'One default handler found and registered: {__default_handler}')
        else:
            self.__logger.warn(f'Multiple default handlers found in controllers: {defaults}')
            __default_handler = defaults[0]
            self.__logger.warn(f'Registered first handler: {__default_handler}')
