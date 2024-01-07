"""The simplest demonstration how controller may work"""
import asyncio

from swiftbots.admin_utils import shutdown_app
from swiftbots.controllers import Controller
from swiftbots.all_types import IBasicView


def print_async(*args, **kwargs):
    return asyncio.to_thread(print, *args, **kwargs)


class BasicController(Controller):

    async def default(self, view: IBasicView, context: IBasicView.Context):
        if context.raw_message == 'exit':
            shutdown_app()
        elif context.raw_message == 'ping':
            await print_async('pong')
        else:
            await print_async(context.raw_message)
