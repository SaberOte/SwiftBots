import asyncio
import aiohttp
import urllib.request
import urllib.parse
import random

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiftbots.types import IChatView


def admin_only_async(func):
    """Decorator. Should wrap controller method to prevent non admin execution"""
    async def wrapper(self, view: 'IChatView', context: 'IChatView.Context'):
        if await view.is_admin_async(context.sender):
            return await func(self, view, context)
        else:
            await view.refuse_async(context)
    return wrapper


async def shutdown_bot_async():
    """
    Shutdown the instance. Won't restart
    """
    task = asyncio.current_task()
    task.cancel()


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
