# noinspection DuplicatedCode
"""
Example how to use admin bot to manage other bots in the same app
"""
from swiftbots.admin_utils import (
    admin_only_async,
    get_bot_names_async,
    shutdown_app,
    shutdown_bot_async,
    start_bot_async,
)
from swiftbots.controllers import Controller
from swiftbots.all_types import ITelegramView


class AdminApi(Controller):

    @admin_only_async
    async def shutdown_bot(self, view: ITelegramView, context: ITelegramView.Context):
        """
        Shutdown some bot in the same app.
        If arguments are empty, called command `exit`. Therefore, exit all bots.
        """
        bot_to_exit = context.arguments
        if not bot_to_exit:
            shutdown_app()
            return
        result = await shutdown_bot_async(bot_to_exit)
        if not result:
            await view.reply_async(f"Bot '{bot_to_exit}' was not found", context)

    @admin_only_async
    async def list_bots(self, view: ITelegramView, context: ITelegramView.Context):
        """
        Send list of all bots in this app
        """
        all_tasks, running, stopped = await get_bot_names_async()

        all_tasks_message = f"All app tasks:\n- {', '.join(all_tasks)}\n" if all_tasks else 'No tasks\n'
        running_tasks_message = f"Running tasks:\n- {', '.join(running)}\n" if running else 'No running tasks\n'
        stopped_tasks = f"Stopped tasks:\n- {', '.join(stopped)}" if stopped else 'No stopped tasks'
        message = all_tasks_message + running_tasks_message + stopped_tasks

        await view.reply_async(message, context)

    @admin_only_async
    async def start_bot(self, view: ITelegramView, context: ITelegramView.Context):
        """
        Try to start the stopped bot
        """
        bot_to_start = context.arguments
        if len(bot_to_start) == 0:
            await view.reply_async('You have to pass a name of the bot to start', context)
            return
        result = await start_bot_async(bot_to_start)
        if result == 1:
            await view.reply_async(f"Bot '{bot_to_start}' is already running", context)
        if result == 2:
            await view.reply_async(f"Bot '{bot_to_start}' was not found", context)

    cmds = {
        'exit': shutdown_bot,
        'list': list_bots,
        'start': start_bot
    }
