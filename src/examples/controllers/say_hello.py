"""
Example of some controller that can just send some dumb messages

1. `cmds` property is a dict where:
   - Key is a command that user pass
   - Value is a function that executes the command.
   Usage example:
   (user): hello
   (bot): Yo!
2. `any` is just a pipe to load there all of query's data.
It's used by only when no one command is not accepted
"""
from src.botcore.bases.base_chat_view import BaseChatView
from src.botcore.bases.base_controller import BaseController

class SayHello(BaseController):
    def __init__(self, bot):
        super().__init__(bot)

    def say_hi(self, view: BaseChatView, context: dict):
        view.answer(f"Yo! {context['sender']}", context)

    def say_truth(self, view: BaseChatView, context: dict):
        view.answer('C is the best programming language ever', context)

    cmds = {
        "hello": say_hi,
    }
    any = say_truth
