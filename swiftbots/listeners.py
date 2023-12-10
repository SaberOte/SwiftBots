from swiftbots.bots import Bot


async def start_async_listener(bot: Bot):
    """
    Launches all bot views, and sends all updates to their message handlers.
    Runs asynchronously.
    """
    listener = bot.view.listen_async
    async for context in listener():
        await bot.message_handler.handle_message_async(bot.view, context)
