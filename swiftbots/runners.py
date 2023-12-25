import asyncio
from traceback import format_exc

from swiftbots.bots import Bot


async def start_async_listener(bot: Bot):
    """
    Launches all bot views, and sends all updates to their message handlers.
    Runs asynchronously.
    """
    async for context in bot.view._listener():
        await bot.message_handler.handle_message_async(bot.view, context)


async def close_bot_async(bot: Bot):
    """
    Call `_close` method of bot to softly close all connections
    """
    try:
        await bot.view._close_async()
    except Exception as e:
        try:
            bot.logger.error(f'Raised an exception `{e}` when a view closing method called:\n{format_exc()}')
        except: pass


async def run_async(bots: list[Bot]):
    tasks: set[asyncio.Task] = set()

    bot_names: dict[str, Bot] = {bot.name: bot for bot in bots}

    for name, bot in bot_names.items():
        task = asyncio.create_task(start_async_listener(bot), name=name)
        tasks.add(task)

    while 1:
        if len(tasks) == 0:
            return
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            name = task.get_name()
            bot = bot_names[name]
            try:
                result = task.result()
                bot.logger.critical(f"Bot {name} was finished with result {result} and restarted")
            except asyncio.CancelledError:
                bot.logger.error(f"Bot {name} was cancelled. Not started again")
                tasks.remove(task)
                await close_bot_async(bot)
                continue
            except Exception as e:
                bot.logger.critical(f"Bot {name} was raised with unhandled exception: {e}",
                                    f"and restarted. Full traceback:\n{format_exc()}")
            await close_bot_async(bot)

            tasks.remove(task)
            new_task = asyncio.create_task(start_async_listener(bot), name=name)
            tasks.add(new_task)
