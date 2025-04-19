import asyncio
import random
from typing import Any, Optional

import httpx

from swiftbots.all_types import ExitApplicationException, StartBotException
from swiftbots.runners import get_all_tasks


def shutdown_app() -> None:
    raise ExitApplicationException("Exited from administrator")


async def shutdown_bot_async(bot_name: str) -> bool:
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
                task.cancel()
                return True
        return False


async def get_bot_names_async() -> tuple[set[str], set[str], set[str]]:
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
    for task_name in all_tasks:
        if task_name.casefold() == bot_name.casefold():
            raise StartBotException(task_name)
    return 2


async def send_telegram_message_async(
    message: str, admin: str, token: str, data: Optional[dict[str, Any]] = None
) -> None:
    if data is None:
        data = {}

    is_traceback = "Traceback" in message and "parse_mode" not in data
    async with httpx.AsyncClient() as session:
        messages = [message[i : i + 4096] for i in range(0, len(message), 4096)]
        for msg in messages:
            send_data = {
                "chat_id": admin,
                "text": f"```\n{msg}\n```" if is_traceback else msg,
            }
            if is_traceback:
                send_data["parse_mode"] = "markdown"
            send_data.update(data)
            await session.post(
                f"https://api.telegram.org/bot{token}/sendMessage", json=send_data
            )


def send_telegram_message(
    message: str, admin: str, token: str, data: Optional[dict[str, Any]] = None
) -> None:
    if data is None:
        data = {}
    is_traceback = "Traceback" in message and "parse_mode" not in data
    messages = [message[i : i + 4096] for i in range(0, len(message), 4096)]
    for msg in messages:
        send_data = {
            "chat_id": admin,
            "text": f"```\n{msg}\n```" if is_traceback else msg,
        }
        if is_traceback:
            send_data["parse_mode"] = "markdown"
        send_data.update(data)
        httpx.post(f"https://api.telegram.org/bot{token}/sendMessage", json=send_data)


async def send_vk_message_async(
    message: str, admin: str, token: str, data: Optional[dict[str, Any]] = None
) -> None:
    if data is None:
        data = {}
    async with httpx.AsyncClient() as session:
        messages = [message[i : i + 4096] for i in range(0, len(message), 4096)]
        for msg in messages:
            send_data = {
                "user_id": admin,
                "message": msg,
                "random_id": random.randint(-(2 ** 31), 2 ** 31),
                "dont_parse_links": 1,
            }
            send_data.update(data)
            url = (
                f"https://api.vk.com/method/messages.send?v=5.199&access_token={token}"
            )
            await session.post(url=url, data=send_data)


def send_vk_message(
    message: str, admin: str, token: str, data: Optional[dict[str, Any]] = None
) -> None:
    if data is None:
        data = {}
    messages = [message[i : i + 4096] for i in range(0, len(message), 4096)]
    for msg in messages:
        send_data = {
            "user_id": admin,
            "message": msg,
            "random_id": random.randint(-(2 ** 31), 2 ** 31),
            "dont_parse_links": 1,
        }
        send_data.update(data)

        httpx.post(f"https://api.vk.com/method/messages.send?v=5.199&access_token={token}", json=send_data)
