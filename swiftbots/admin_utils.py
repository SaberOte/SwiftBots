import asyncio
import aiohttp
import urllib.request
import urllib.parse
import random

from typing import TYPE_CHECKING

from swiftbots.runners import get_all_tasks
from swiftbots.types import StartBotException, ExitApplicationException

if TYPE_CHECKING:
    from swiftbots.types import IChatView


def admin_only_async(func):
    """Decorator. Should wrap controller method to prevent non admin execution"""
    async def wrapper(self, view: 'IChatView', context: 'IChatView.Context'):
        """admin_only_wrapper"""
        if await view.is_admin_async(context.sender):
            return await func(self, view, context)
        else:
            await view.refuse_async(context)
    return wrapper


def shutdown_app() -> None:
    raise ExitApplicationException("Exited from administrator")


async def shutdown_bot_async(bot_name: str = None) -> bool:
    """
    Shutdown the instance. Won't restart.
    If param bot_name is provided, it closes the current task.
    Otherwise, it closes the bot with name `bot_name`
    :return: True if the bot was stopped, False if not found
    """
    if bot_name.casefold() not in [task.casefold() for task in get_all_tasks()]:
        return False
    else:
        tasks = asyncio.all_tasks()
        for task in tasks:
            if task.get_name().casefold() == bot_name.casefold():
                task.cancel(f'Bot {bot_name} was stopped by administrator.')
                return True
        return False


async def get_bot_names_async() -> (set[str], set[str], set[str]):
    """
    :returns: 1. a set of all the tasks in app;
    2. set of running tasks;
    3. set of stopped tasks
    """
    app_tasks = get_all_tasks()

    running_task_instances = asyncio.all_tasks()
    all_running_tasks = {task.get_name() for task in running_task_instances}
    # It returns also system tasks, we don't need it
    stopped_tasks = app_tasks - all_running_tasks
    running_tasks = app_tasks - stopped_tasks
    return app_tasks, running_tasks, stopped_tasks


async def start_bot_async(bot_name: str) -> int:
    """
    Try to start bot. It must be already stopped.
    :returns: exception `StartBotException` if bot was successfully asked started.
    1 if the bot already is running.
    2 if there is no such bot name
    """
    tasks = asyncio.all_tasks()
    for task in tasks:
        if task.get_name().casefold() == bot_name.casefold():
            return 1

    all_tasks = get_all_tasks()
    for task in all_tasks:
        if task.casefold() == bot_name.casefold():
            raise StartBotException(task)
    return 2


async def send_telegram_message_async(message: str, admin: str, token: str) -> None:
    async with aiohttp.ClientSession() as session:
        data = {
            "chat_id": admin,
            "text": message
        }
        await session.post(f'https://api.telegram.org/bot{token}/sendMessage', json=data)


def send_telegram_message(message: str, admin: str, token: str) -> None:
    data = {
        "chat_id": admin,
        "text": message
    }
    encoded_data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(f'https://api.telegram.org/bot{token}/sendMessage', data=encoded_data, method='POST')
    urllib.request.urlopen(req)


async def send_vk_message_async(message: str, admin: str, token: str) -> None:
    async with aiohttp.ClientSession() as session:
        data = {
            'user_id': admin,
            'message': message,
            'random_id': random.randint(-2 ** 31, 2 ** 31)
        }
        url = f'https://api.vk.com/method/messages.send?v=5.199&access_token={token}'
        await session.post(url=url, data=data)


def send_vk_message(message: str, admin: str, token: str) -> None:
    data = {
        'user_id': admin,
        'message': message,
        'random_id': random.randint(-2 ** 31, 2 ** 31)
    }
    encoded_data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(f'https://api.vk.com/method/messages.send?v=5.199&access_token={token}',
                                 data=encoded_data, method='POST')
    urllib.request.urlopen(req)
