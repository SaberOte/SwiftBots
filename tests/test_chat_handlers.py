from typing import Optional

import pytest

from swiftbots.message_handlers import compile_command_as_regex, CompiledChatCommand, insert_trie, search_best_command_match, Trie


def try_on(trie: Trie, word: str) -> Optional[int]:
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
