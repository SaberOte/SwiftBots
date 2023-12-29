# noinspection DuplicatedCode
"""
Example how to use admin bot to manage other bots in the same app
"""
import asyncio

from swiftbots.types import ITelegramView
from swiftbots.controllers import Controller
from swiftbots.admin_utils import admin_only_async, shutdown_bot_async, get_list_bots_async


class AdminApi(Controller):

    @admin_only_async
    async def shutdown_bot(self, view: ITelegramView, context: ITelegramView.Context):
        """
        Shutdown some bot in the same app.
        If arguments are empty, called command `exit`. Therefore, exit this bot itself
        """
        bot_to_exit = context.arguments
        result = await shutdown_bot_async(bot_to_exit)
        if not result:
            await view.send_async(f'Bot {bot_to_exit} was not found', context)

    @admin_only_async
    async def list_bots(self, view: ITelegramView, context: ITelegramView.Context):
        """
        Send list of all bots in this app
        """
        bots = await get_list_bots_async()
        await view.send_async(', '.join(bots), context)

    cmds = {
        'exit': shutdown_bot,
        'list': list_bots
    }
