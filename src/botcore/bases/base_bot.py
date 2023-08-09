"""
BOT MUST:
1. Be launch in docker container single and standalone
2. Have at least 1 controller
3. May have views or tasks
4. If it has views, it pins views commands with controller methods
5. If it has tasks, each one has to have: task name, calling schedule, controller's method to call
"""
import re
import asyncio
from abc import ABC
from sys import stderr
from typing import Callable
from traceback import format_exc
from src.botcore.bases.base_view import BaseView, ViewContext


class BaseBot(ABC):
    # "subscription" for controllers. Each command pinned with some controller method
    commands: {str: Callable} = {}
    # subscription for any received content. Calls when no one command wasn't recognized (Optional)
    any: Callable = None
    # it must be no or just one view. Using for interacting with users or other creatures.
    view: BaseView = None
    # messages received from other bots or tasks
    # TODO: enable tasks and other bots interaction
    # inner_commands: {str: str} = {}
    compiled_commands_patterns = {}

    def init(self):
        """
        Preparing a bot for execution.
        Launches with its own communicator and thread with port listening
        """


    def get_name(self) -> str:
        return self.__module__.split('.')[-1]

    async def message_handler(self, listener):
        async for context in listener():
            context: ViewContext = context
            message = context.message
            lower_message = message.lower()
            # check exact coincidence
            if lower_message in self.commands:
                method = self.commands[lower_message]
                method(view=self.view, context=context)
                continue
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

    async def init_listen(self):
        """
        Starts to listen own port and starts to listen outer resources with view.listen method.
        This method starts infinite loop and never returns anything
        """
        # TODO: method is too large. Minimize that
        # compile all regex patterns to faster search in command handlers
        for name in self.commands:
            escaped_name = re.escape(name)
            pattern = re.compile(rf'^({escaped_name})\s+(\S+)$', re.IGNORECASE)
            self.compiled_commands_patterns[name] = pattern

        if self.view is not None:
            listeners = self.view.get_listeners()
        else:
            listeners = {}
        # TODO: enable port listener here
        '''
        listeners['port_listener'] = self.listen_port
        '''
        handlers = {}
        for name in listeners:
            handlers[name] = lambda: self.message_handler(listeners[name])

        # TODO: develop low level handlers: port listener, tasks listener
        # handlers.update(get_low_level_handlers())

        tasks = set()
        for name in handlers:
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
