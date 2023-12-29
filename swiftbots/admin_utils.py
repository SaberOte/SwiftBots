import asyncio

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiftbots.types import IChatView


def admin_only_async(func):
    """Decorator. Should wrap controller method to prevent non admin execution"""
    async def wrapper(self, view: 'IChatView', context: 'IChatView.Context'):
        if view.is_admin(context.sender):
            await view.refuse_async(context)
        else:
            return await func(self, view, context)
    return wrapper


async def shutdown_bot_async():
    """
    Shutdown the instance. Won't restart
    """
    task = asyncio.current_task()
    task.cancel()
