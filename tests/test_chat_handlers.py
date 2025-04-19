import re
from typing import Callable

import pytest

from swiftbots.message_handlers import compile_command_as_regex, CompiledChatCommand


FINAL_INDICATOR = '**'
type Trie = dict[str, Trie | CompiledChatCommand]


def insert_trie(trie: Trie, word: str, command: CompiledChatCommand) -> None:
    for ch in word:
        trie = trie.setdefault(ch, {})
    trie[FINAL_INDICATOR] = command


def search_trie(trie: Trie, word: str) -> Trie | None:
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


def search_best_command_match(trie: Trie, word: str) -> tuple[CompiledChatCommand | None, re.Match | None]:
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


def try_on(trie: Trie, word: str) -> None | int:
    command, match = search_best_command_match(trie, word)
    if command:
        return command.method()
    return None


class TestChatHandlers:
    @pytest.mark.timeout(3)
    def test_trie_functions(self):
        trie = {}

        def insert(command_name: str, result: int) -> None:
            insert_trie(trie, command_name, CompiledChatCommand(command_name, lambda: result, compile_command_as_regex(command_name), [], []))

        insert("apple", 1)
        insert("cranberry", 2)
        insert("apple cranberry", 3)

        assert try_on(trie, "apple") == 1
        assert try_on(trie, "cranberry") == 2
        assert try_on(trie, "apple cranberry") == 3
        assert try_on(trie, "apple pear") == 1
        assert try_on(trie, "applecherry") is None
        assert try_on(trie, "apple cherry") == 1
        assert try_on(trie, "apple cranberrycherry") == 1
        assert try_on(trie, "a") is None
        assert try_on(trie, "cherry") is None
        assert try_on(trie, "cherry apple") is None
        assert try_on(trie, "pple") is None
