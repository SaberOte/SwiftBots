"""Minimal demonstration of the simple chatbot view in the terminal"""
import asyncio

from swiftbots.views import BasicView


def input_async(*args, **kwargs):
    return asyncio.to_thread(input, *args, **kwargs)


class SimpleView(BasicView):
    """
    Pretty simple example of Basic View usage.
    Though Chat View is better option here
    """

    async def listen_async(self):
        print("Welcome in the command line chat! Good day, Friend!")
        while True:
            message = await input_async('-> ')
            yield self.PreContext(message)
