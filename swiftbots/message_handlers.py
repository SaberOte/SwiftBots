import re
from collections.abc import Coroutine
from typing import TYPE_CHECKING, Any, Optional, Union

from swiftbots.functions import resolve_function_args
from swiftbots.types import DecoratedCallable

if TYPE_CHECKING:
    from swiftbots.chats import Chat


__trimmer = re.compile(r"\s+$")


class ChatMessageHandler:
    def __init__(self,
                 commands: list[str],
                 function: DecoratedCallable,
                 whitelist_users: Optional[list[Union[str, int]]],
                 blacklist_users: Optional[list[Union[str, int]]]):
        self.commands = commands
        self.function = function
        self.whitelist_users = None if whitelist_users is None else [str(x).casefold() for x in whitelist_users]
        self.blacklist_users = None if blacklist_users is None else [str(x).casefold() for x in blacklist_users]


class CompiledChatCommand:
    def __init__(
        self,
        command_name: str,
        method: DecoratedCallable,
        pattern: re.Pattern,
        whitelist_users: Optional[list[str]],
        blacklist_users: Optional[list[str]]
    ):
        self.command_name = command_name
        self.method = method
        self.pattern = pattern
        self.whitelist_users = whitelist_users
        self.blacklist_users = blacklist_users


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
    handlers: list[ChatMessageHandler],
) -> list[CompiledChatCommand]:
    compiled_commands = [
        CompiledChatCommand(
            command_name=command,
            method=handler.function,
            pattern=compile_command_as_regex(command),
            blacklist_users=handler.blacklist_users,
            whitelist_users=handler.whitelist_users
        )
        for handler in handlers
        for command in handler.commands
    ]
    return compiled_commands


def is_user_allowed(user: Union[str, int],
                    whitelist_users: Optional[list[str]],
                    blacklist_users: Optional[list[str]]
                    ) -> bool:
    user = str(user).casefold()
    if blacklist_users is not None:
        return user not in blacklist_users
    if whitelist_users is not None:
        return user in whitelist_users
    return True


def handle_message(
        message: str,
        chat: 'Chat',
        commands: list[CompiledChatCommand],
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

        if is_user_allowed(chat.sender, best_matched_command.whitelist_users, best_matched_command.blacklist_users):
            return method(**args)
        else:
            return chat.refuse_async()

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
