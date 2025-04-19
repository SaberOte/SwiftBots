import re
from collections.abc import Coroutine
from typing import TYPE_CHECKING, Any, Optional, Union

from swiftbots.functions import resolve_function_args
from swiftbots.types import DecoratedCallable

if TYPE_CHECKING:
    from swiftbots.chats import Chat


FINAL_INDICATOR = '**'


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


type Trie = dict[str, Union[Trie, CompiledChatCommand]]


def insert_trie(trie: Trie, word: str, command: CompiledChatCommand) -> None:
    for ch in word:
        trie = trie.setdefault(ch, {})
    trie[FINAL_INDICATOR] = command


def search_trie(trie: Trie, word: str) -> Optional[Trie]:
    """
    Searches the first full command match in the trie.
    """
    for ch in word:
        trie = trie.get(ch)
        if trie is None:
            return None
        if FINAL_INDICATOR in trie:
            return trie
    return None


def search_best_command_match(trie: Trie, word: str) -> tuple[Optional[CompiledChatCommand], Optional[re.Match]]:
    matches = []
    sub_word = word
    while trie:
        trie = search_trie(trie, sub_word)
        if trie:
            command: CompiledChatCommand = trie[FINAL_INDICATOR]
            matches.append(command)
            sub_word = word[len(command.command_name):]
    for command in reversed(matches):
        match = command.pattern.fullmatch(word)
        if match:
            return command, match
    return None, None


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


def compile_command_as_regex(name: str) -> re.Pattern:
    """
    Compile with regex patterns all the command names for the faster search.
    Pattern is:
    1. Begins with the NAME OF COMMAND (case-insensitive).
    2. Then any whitespace characters [ \f\n\r\t\v] (zero or more).
    3. Then the rest of the text (let's name it arguments). Marks as group 1.
    Group 1 is optional. If there is empty group 1, then the message is entirely match the command
    """
    escaped_name = re.escape(name)
    return re.compile(rf"^{escaped_name}(?:\s+(.*))?$", re.IGNORECASE | re.DOTALL)


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
        trie: Trie,
        default_handler_func: Optional[DecoratedCallable],
        all_deps: dict[str, Any]
) -> Coroutine:
    best_matched_command, match = search_best_command_match(trie, message.lower())

    if best_matched_command and not is_user_allowed(chat.sender, best_matched_command.whitelist_users, best_matched_command.blacklist_users):
        return chat.refuse_async()

    arguments = ""
    # check if the command has arguments like `ADD NOTE apple, cigarettes, cheese`,
    # where `ADD NOTE` is a command and the rest is arguments
    if match:
        message_without_command = match.group(1)
        if message_without_command:
            arguments = message_without_command

    # Found the command. Call the method attached to the command
    if best_matched_command:
        method = best_matched_command.method
        command_name = best_matched_command.command_name
        all_deps['raw_message'] = message
        all_deps['arguments'] = arguments
        all_deps['args'] = arguments
        all_deps['command'] = command_name
        all_deps['message'] = arguments
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
