import asyncio

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiftbots.types import IChatView


def admin_only_async(func):
    """Decorator. Should wrap controller method to prevent non admin execution"""
    async def wrapper(self, view: 'IChatView', context: 'IChatView.Context'):
        if view._admin is not None:
            if str(context.sender) != str(view._admin):
                await view.refuse_async(context)
            else:
                return await func(self, view, context)
        else:
            view._logger.error('admin_only decorator requires `_admin` property in view')
            await view.error_async(context)
    return wrapper


async def shutdown_bot_async():
    """
    Shutdown the instance. Won't restart
    """
    task = asyncio.current_task()
    task.cancel()
