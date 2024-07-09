import asyncio
from traceback import format_exc
from typing import Any, Dict, Set

from swiftbots.all_types import (
    ExitApplicationException,
    ExitBotException,
    IScheduler,
    RestartListeningException,
    StartBotException,
)
from swiftbots.app.container import AppContainer
from swiftbots.bots import Bot, build_scheduler, stop_bot_async
from swiftbots.controllers import soft_close_controllers_in_bots_async
from swiftbots.functions import call_raisable_function_async, decompose_bot_as_dependencies, resolve_function_args
from swiftbots.utils import ErrorRateMonitor

__ALL_TASKS: Set[str] = set()
__SCHEDULER_TASK_NAME = '__sched__'


def get_all_tasks() -> Set[str]:
    return __ALL_TASKS


async def start_async_listener(bot: Bot) -> None:
    """
    Launches all bot listeners, and sends all updates to their handlers.
    Runs asynchronously.
    """
    err_monitor = ErrorRateMonitor(cooldown=60)
    generator = bot.listener_func()
    while True:
        try:
            output = await generator.__anext__()
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
                    f"Stopping bot."
                )
            rate = err_monitor.evoke()
            if rate > 5:
                await bot.logger.error_async(f"Bot {bot.name} sleeps for 30 seconds.")
                await asyncio.sleep(30)
                err_monitor.error_count = 3
            generator = bot.listener_func()
            continue

        async def handle() -> Any:  # noqa: ANN401
            deps = decompose_bot_as_dependencies(bot)
            deps.update(output)
            args = resolve_function_args(bot.handler_func, deps)
            return await bot.handler_func(**args)
        await call_raisable_function_async(handle, bot)


async def start_bot(bot: Bot, scheduler: IScheduler) -> None:
    bot.enable()
    build_scheduler([bot], scheduler)
    await start_async_listener(bot)


async def start_async_loop(app_container: AppContainer) -> None:
    bots = app_container.bots
    sched = app_container.scheduler
    tasks: Set[asyncio.Task] = set()

    bots_dict: Dict[str, Bot] = {bot.name: bot for bot in bots}
    global __ALL_TASKS
    __ALL_TASKS = set(bots_dict.keys())

    # Create tasks for the bots' views
    for name, bot in bots_dict.items():
        task = asyncio.create_task(start_async_listener(bot), name=name)
        tasks.add(task)
    # Create a task for the scheduler
    tasks.add(
        asyncio.create_task(sched.start(), name=__SCHEDULER_TASK_NAME)
    )

    while True:
        # if no bots launched, then close the app
        if not any(filter(lambda t: t.get_name() != __SCHEDULER_TASK_NAME, tasks)):
            await soft_close_controllers_in_bots_async(list(bots_dict.values()))
            await app_container.logger.report_async("Bots application's closed. The reason is no bots launched now.")
            return
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            name = task.get_name()
            logger = bots_dict[name].logger if name != __SCHEDULER_TASK_NAME else app_container.logger
            try:
                result = task.result()
                await logger.critical_async(
                    f"Bot {name} is finished with result {result} and restarted"
                )
            except (asyncio.CancelledError, ExitBotException) as ex:
                if isinstance(ex, asyncio.CancelledError):
                    await logger.warning_async(
                        f"Bot {name} is cancelled. Not started again"
                    )
                    await logger.report_async(f"Bot {name}'s exited")
                elif isinstance(ex, ExitBotException):
                    await logger.error_async(
                        f"Bot {name} is exited with message: {ex}"
                    )
                bot = bots_dict[name]
                await stop_bot_async(bot, sched)
                tasks.remove(task)
            except RestartListeningException:
                tasks.remove(task)
                bot = bots_dict[name]
                new_task = asyncio.create_task(start_async_listener(bot), name=name)
                tasks.add(new_task)
            except StartBotException as ex:
                # Special exception instance for starting bots from admin panel

                # At the start, dispose the task of caller bot and create new.
                # The caller task is no longer reusable because an exception was raised.
                tasks.remove(task)
                bot = bots_dict[name]
                new_task = asyncio.create_task(start_async_listener(bot), name=name)
                tasks.add(new_task)

                # Start a new bot with the name from an exception
                try:
                    bot_name_to_start = str(ex)
                    bot_to_start = bots_dict[str(ex)]
                    new_task = asyncio.create_task(
                        start_bot(bot_to_start, sched), name=bot_name_to_start
                    )
                    tasks.add(new_task)
                except Exception as e:
                    await logger.critical_async(
                        f"Couldn't start bot {ex}. Exception: {e}"
                    )
            except ExitApplicationException:
                # close all bots
                for a_task in tasks:
                    bot_name_to_exit = a_task.get_name()
                    if bot_name_to_exit != __SCHEDULER_TASK_NAME:
                        bot_to_exit = bots_dict[bot_name_to_exit]
                        await stop_bot_async(bot_to_exit, sched)
                        await bot_to_exit.logger.report_async(
                            f"Bot {bot_to_exit.name}'s exited"
                        )
                await logger.report_async("Bots application's closed")
                return


def run_async(container: AppContainer) -> None:
    asyncio.run(start_async_loop(container))
