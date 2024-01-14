import asyncio
from traceback import format_exc

from swiftbots.all_types import (
    ExitApplicationException,
    ExitBotException,
    IChatView,
    IContext,
    RestartListeningException,
    StartBotException,
)
from swiftbots.bots import Bot, soft_close_bot_async
from swiftbots.controllers import soft_close_controllers_in_bots_async
from swiftbots.utils import ErrorRateMonitor

__ALL_TASKS: set[str] = set()


def get_all_tasks() -> set[str]:
    return __ALL_TASKS


async def delegate_to_handler_async(bot: Bot, context: IContext) -> None:
    assert bot.view and bot.message_handler, (
        "Method delegate_to_handler_async can't be called "
        "without a view or message handler in a bot"
    )
    try:
        await bot.message_handler.handle_message_async(bot.view, context)
    except (AttributeError, TypeError, KeyError, AssertionError) as e:
        await bot.logger.critical_async(
            f"Fix the code! Critical `{e.__class__.__name__}` "
            f"raised:\n{e}.\nFull traceback:\n{format_exc()}"
        )
        if isinstance(bot.view, IChatView):
            await bot.view.error_async(context)
    except Exception as e:
        await bot.logger.exception_async(
            f"Bot {bot.name} was raised with unhandled `{e.__class__.__name__}` "
            f"and kept on working:\n{e}.\nFull traceback:\n{format_exc()}"
        )
        if isinstance(bot.view, IChatView):
            await bot.view.error_async(context)


async def start_async_listener(bot: Bot) -> None:
    """
    Launches all bot views, and sends all updates to their message handlers.
    Runs asynchronously.
    """
    assert (
        bot.view
    ), "Method start async listener can't be called without a view in a bot"

    err_monitor = ErrorRateMonitor(cooldown=60)
    generator = bot.view.listen_async()
    while True:
        try:
            pre_context = await generator.__anext__()
        # except (AttributeError, TypeError, KeyError, AssertionError) as e:
        #     await bot.logger.critical_async(f"Fix the code! Critical {e.__class__.__name__} "
        #                                     f"raised: {e}. Full traceback:\n{format_exc()}")
        #     continue
        except RestartListeningException:
            continue
        except Exception as e:
            await bot.logger.exception_async(
                f"Bot {bot.name} was raised with unhandled `{e.__class__.__name__}`"
                f" and kept on listening:\n{e}.\nFull traceback:\n{format_exc()}"
            )
            if err_monitor.since_start < 3:
                raise ExitBotException(
                    f"Bot {bot.name} raises immediately after start listening. "
                    f"Shutdowning this."
                )
            rate = err_monitor.evoke()
            if rate > 5:
                await bot.logger.error_async(f"Bot {bot.name} sleeps for 30 seconds.")
                await asyncio.sleep(30)
                err_monitor.error_count = 3
            generator = bot.view.listen_async()
            continue

        await delegate_to_handler_async(bot, pre_context)


async def start_bot(bot: "Bot") -> None:
    # if bot.tasks:
    #     for task in bot.tasks:
    if bot.view:
        await start_async_listener(bot)


async def run_async(bots: list[Bot]) -> None:
    tasks: set[asyncio.Task] = set()

    bots_dict: dict[str, Bot] = {bot.name: bot for bot in bots}
    global __ALL_TASKS
    __ALL_TASKS = set(bots_dict.keys())

    for name, bot in bots_dict.items():
        task = asyncio.create_task(start_bot(bot), name=name)
        tasks.add(task)

    while 1:
        if len(tasks) == 0:
            return
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            name = task.get_name()
            bot = bots_dict[name]
            try:
                result = task.result()
                await bot.logger.critical_async(
                    f"Bot {name} is finished with result {result} and restarted"
                )
            except (asyncio.CancelledError, ExitBotException) as ex:
                if isinstance(ex, asyncio.CancelledError):
                    await bot.logger.warning_async(
                        f"Bot {name} is cancelled. Not started again"
                    )
                    await bot.logger.report_async(f"Bot {name}'s exited")
                elif isinstance(ex, ExitBotException):
                    await bot.logger.error_async(
                        f"Bot {name} is exited with message: {ex}"
                    )
                tasks.remove(task)
            except RestartListeningException:
                tasks.remove(task)
                new_task = asyncio.create_task(start_bot(bot), name=name)
                tasks.add(new_task)
            except StartBotException as ex:
                # Special exception instance for starting bots from admin panel

                # At start, dispose the task of caller bot and create new.
                # The caller task is no longer reusable because an exception was raised.
                tasks.remove(task)
                new_task = asyncio.create_task(start_bot(bot), name=name)
                tasks.add(new_task)

                # Start a new bot with the name from an exception
                try:
                    bot_name_to_start = str(ex)
                    bot_to_start = bots_dict[str(ex)]
                    new_task = asyncio.create_task(
                        start_bot(bot_to_start), name=bot_name_to_start
                    )
                    tasks.add(new_task)
                except Exception as e:
                    await bot.logger.critical_async(
                        f"Couldn't start bot {ex}. Exception: {e}"
                    )
            except ExitApplicationException:
                # close controllers
                await soft_close_controllers_in_bots_async(list(bots_dict.values()))

                # close bots already
                for a_task in tasks:
                    bot_name_to_exit = a_task.get_name()
                    bot_to_exit = bots_dict[bot_name_to_exit]
                    await soft_close_bot_async(bot_to_exit)
                    await bot_to_exit.logger.report_async(
                        f"Bot {bot_to_exit.name}'s exited"
                    )
                await bot.logger.report_async("Bots application's closed")
                return
