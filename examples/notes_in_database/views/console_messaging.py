"""Minimal demonstration of the simple chatbot view in the terminal"""
import asyncio

from swiftbots.views import ChatPreContext, ChatView


def input_async(*args, **kwargs):
    return asyncio.to_thread(input, *args, **kwargs)


class ConsoleView(ChatView):
    """
    Pretty simple example of Chat View usage.
    """

    async def listen_async(self):
        print("Welcome in the command line chat! Good day, Friend!")
        # print("Type expression to solve like `add 2 2` or `- 70 1`")
        while True:
            message = await input_async('-> ')
            yield ChatPreContext(message, 'der Hund')

    async def send_async(self, message, user, data: dict = None):
        print(message)
