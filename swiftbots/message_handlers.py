import re
from collections.abc import Coroutine
from typing import TYPE_CHECKING, Any, List, Optional

from swiftbots.functions import resolve_function_args
from swiftbots.types import DecoratedCallable

if TYPE_CHECKING:
    from swiftbots.chats import Chat


__trimmer = re.compile(r"\s+$")


class ChatMessageHandler1:
    def __init__(self, commands: List[str], function: DecoratedCallable):
        self.commands = commands
        self.function = function


class CompiledChatCommand:
    def __init__(
        self,
        command_name: str,
        method: DecoratedCallable,
        pattern: re.Pattern,
    ):
        self.command_name = command_name
        self.method = method
        self.pattern = pattern


def compile_command_as_regex(name: str) -> re.Pattern:
    """
    Compile with regex patterns all the command names for the faster search.
    Pattern is:
    1. Begins with the NAME OF COMMAND (case-insensitive). Marks as group 1.
    2. Then any whitespace characters [ \f\n\r\t\v] (zero or more). Marks as group 3.
    3. Then the rest of the text (let's name it arguments). Marks as group 4.
    Group 3 and group 4 are optional. If there is empty group 4, then the message is entirely match the command
    """
    escaped_name = re.escape(name)
    return re.compile(rf"^({escaped_name})((\s+)(.*))?$", re.IGNORECASE | re.DOTALL)


def compile_chat_commands(
    handlers: List[ChatMessageHandler1],
) -> List[CompiledChatCommand]:
    compiled_commands = [
        CompiledChatCommand(
            command_name=command,
            method=handler.function,
            pattern=compile_command_as_regex(command),
        )
        for handler in handlers
        for command in handler.commands
    ]
    return compiled_commands


def handle_message(
        message: str,
        chat: 'Chat',
        commands: List[CompiledChatCommand],
        default_handler_func: Optional[DecoratedCallable],
        all_deps: dict[str, Any]
) -> Coroutine:
    arguments: str = ""
    best_match_rank = 0
    best_matched_command: Optional[CompiledChatCommand] = None

    # check if the command has arguments like `ADD NOTE apple, cigarettes, cheese`,
    # where `ADD NOTE` is a command and the rest is arguments
    for command in commands:
        pattern: re.Pattern = command.pattern
        match = pattern.match(message)

        if match:
            message_without_command = match.group(4)
            if not message_without_command:
                # the entire message matches the command
                best_matched_command = command
                arguments = ""
                break
            # the message matches partly. there are arguments. Despite the match, try to find a better match
            match_rank = len(command.command_name)
            if match_rank > best_match_rank:
                best_match_rank = match_rank
                best_matched_command = command
                arguments = message_without_command

    # Found the command. Call the method attached to the command
    if best_matched_command:
        arguments = __trimmer.sub("", arguments)
        method = best_matched_command.method
        command_name = best_matched_command.command_name
        all_deps['raw_message'] = message
        all_deps['arguments'] = arguments
        all_deps['args'] = arguments
        all_deps['command'] = command_name
        all_deps['message'] = arguments
        # del all_deps['message']  # Maybe, I'll delete 'message' because it can mislead
        args = resolve_function_args(method, all_deps)
        return method(**args)

    elif default_handler_func is not None:  # No matches. Use default handler
        method = default_handler_func
        all_deps['raw_message'] = message
        all_deps['arguments'] = message
        all_deps['args'] = message
        all_deps['command'] = ''
        args = resolve_function_args(method, all_deps)
        return method(**args)

    else:  # No matches and default handler. Send `unknown message`
        return chat.unknown_command_async()
