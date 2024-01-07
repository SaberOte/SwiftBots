import re
from collections.abc import Callable

from swiftbots.types import (
    IBasicMessageHandler,
    IChatMessageHandler,
    IChatView,
    IContext,
    IController,
    ILogger,
    IView,
)


class BasicMessageHandler(IBasicMessageHandler):
    """"""
    __doc__ += IBasicMessageHandler.__doc__

    __controller: IController
    __logger: ILogger

    def __init__(self, controllers: list[IController], logger: ILogger):
        self.__logger = logger
        self.__logger.info('Initializing BasicMessageHandler')
        assert len(controllers) == 1, 'Basic message handler can serve only 1 controller'
        controller = controllers[0]
        assert isinstance(controller, IController)
        assert controller.default is not None, \
            'Controller must have `default` method if serves by basic message handler'
        self.__controller = controller

    async def handle_message_async(self, view: IView, context: IContext) -> None:
        message = context['message']
        del context['message']
        new_context = view.Context(**context, raw_message=message)
        # await do_method_async(self.__controller.default.__func__, self.__controller, view, new_context)
        await self.__controller.default(view, new_context)


class ChatMessageHandler(IChatMessageHandler):
    """"""
    __doc__ += IChatMessageHandler.__doc__

    class ControllerCommand:
        command_name: str
        method: Callable
        pattern: re.Pattern
        controller: IController

        def __init__(self, command_name: str, method: Callable, pattern: re.Pattern, controller: IController):
            self.command_name = command_name
            self.method = method
            self.pattern = pattern
            self.controller = controller

    __trimmer = re.compile(r'\s+$')
    __controllers: list[IController]
    __default_controller: IController | None = None
    __logger: ILogger
    __commands: list[ControllerCommand] = None

    def __init__(self, controllers: list[IController], logger: ILogger):
        self.__logger = logger
        self.__logger.info('Initializing ChatMessageHandler')
        self.__controllers = controllers
        self.__commands = []

        self.__build_commands(self.__controllers)
        commands_represent = (
            '\n'.join([f'"{command.command_name}": ({command.controller.__class__.__name__}){command.method}'
                       for command in self.__commands]))
        self.__logger.info(f'Initialized commands:\n{commands_represent}')

        self.__register_default_controller()

    def use_as_default(self, controller: IController | None) -> None:
        """
        Define the method that will be called when no one
        commands was fitted to process the message.
        May be passed None if it's needed to disable any default handler
        :param controller: Function for defining the default command handler,
        or None to disable any default commands
        """
        self.__default_controller = controller
        if controller is not None:
            self.__logger.info(f'Registered default handler directly: {self.__default_controller}')
        else:
            self.__logger.info('Unregistered default handler directly')

    async def handle_message_async(self, view: IChatView, context: IChatView.PreContext) -> None:
        """
        Receive the command and send it to one of the controllers to execute.
        If no one fitted commands found, then send a message to a default handler.
        If it's no default handler, reject to execute command.
        :param view: View object
        :param context: pre context. Must have a message field.
        """
        message: str = context.message
        arguments: str = ''
        best_match_rank = 0
        best_matched_command: 'ChatMessageHandler.ControllerCommand' | None = None

        # check if the command has arguments like `ADD NOTE apple, cigarettes, cheese`,
        # where `ADD NOTE` is a command and the rest is arguments
        for command in self.__commands:
            pattern: re.Pattern = command.pattern
            match = pattern.match(message)

            if match:
                message_without_command = match.group(4)
                if not message_without_command:  # the entire message matches the command
                    best_matched_command = command
                    arguments = ''
                    break
                # message matches partly. there are arguments. Despite the match, try to find better match
                match_rank = len(command.command_name)
                if match_rank > best_match_rank:
                    best_match_rank = match_rank
                    best_matched_command = command
                    arguments = message_without_command

        if best_matched_command:
            arguments = self.__trimmer.sub('', arguments)
            method = best_matched_command.method
            command_name = best_matched_command.command_name
            controller = best_matched_command.controller

        elif self.__default_controller is not None:  # No matches. Use default controller method
            command_name = arguments = message
            controller = self.__default_controller
            method = controller.default.__func__

        else:  # No matches and default methods. Send `unknown message`
            await view.unknown_command_async(context)
            return

        del context['message']
        new_context = view.Context(raw_message=message, arguments=arguments, command=command_name, **context)
        # await do_method_async(method, controller, view, new_context)
        await method(controller, view=view, context=new_context)

    def __build_commands(self, controllers: list[IController]) -> None:
        for controller in controllers:
            for command in controller.cmds:
                controller_command = self.ControllerCommand(command,
                                                            controller.cmds[command],
                                                            self.__compile_command_as_regex(command),
                                                            controller)
                self.__commands.append(controller_command)

    @staticmethod
    def __compile_command_as_regex(name: str) -> re.Pattern:
        """
        Compile with regex patterns all command names to faster search.
        Pattern is:
        1. Begins with NAME OF COMMAND (case-insensitive). Marks as group 1.
        2. Then any whitespace characters [ \f\n\r\t\v] (zero or more). Marks as group 3.
        3. Then the rest of the text. Marks as group 4.
        Group 3 and group 4 are optional. If there is empty group 4, then the message is entirely match a command
        """
        escaped_name = re.escape(name)
        return re.compile(rf'^({escaped_name})((\s+)(.*))?$', re.IGNORECASE | re.DOTALL)

    def __register_default_controller(self) -> None:
        """
        Choose the default handler from all controllers.
        If that's only one `default` method found, it will be registered as default handler.
        If that's no `default` methods founds, default handler stays None and
        unfitted commands will be rejected to execute (`unknown_command_async` method of the view will be called).
        If that's more than 1 `default` method found, first found will be registered.
        """
        defaults = list(filter(lambda c: c.default is not None, self.__controllers))
        if len(defaults) == 0:
            self.__logger.info('No default handlers in controllers')
        elif len(defaults) == 1:
            self.__default_controller = defaults[0]
            self.__logger.info(f'One default handler found and registered: {self.__default_controller}')
        else:
            self.__logger.warn(f'Multiple default handlers found in controllers: {defaults}')
            self.__default_controller = defaults[0]
            self.__logger.warn(f'Registered handler: {self.__default_controller}')
