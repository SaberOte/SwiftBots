import asyncio

from typing import Optional

from swiftbots.types import IView, IController, IMessageHandler, ILogger


class Bot:
    """A storage of controllers and views"""

    name: str

    view_class: type[IView]
    controller_classes: list[type[IController]]
    message_handler_class: Optional[type[IMessageHandler]]

    view: IView
    controllers: list[IController]
    message_handler: IMessageHandler
    logger: ILogger

    def __init__(self, view_class: type[IView], controller_classes: list[type[IController]],
                 message_handler_class: Optional[type[IMessageHandler]], logger: ILogger, name: str):
        self.view_class = view_class
        self.controller_classes = controller_classes
        self.message_handler_class = message_handler_class
        self.logger = logger
        self.name = name

    async def shutdown_bot_async(self):
        """
        Shutdown the instance. Won't restart
        """
        self.logger.critical("Bot task was cancelled.")
        try:
            await self.view._close_async()
        except Exception as e:
            self.logger.critical("Raised an exception when the bot task is cancelling: \n", e)

        task: asyncio.tasks.Task = await asyncio.current_task()
        task.cancel()


def _set_views(bots: list[Bot]) -> None:
    """
    Instantiate and set views
    """
    for bot in bots:
        bot.view = bot.view_class()
        bot.view.init(bot, bot.logger)


def _set_controllers(bots: list[Bot]) -> None:
    """
    Instantiate and set to the bot controllers, each one must be singleton
    """
    controller_memory: list[IController] = []
    for bot in bots:
        controllers_to_add: list[IController] = []
        controller_types = bot.controller_classes

        for controller_type in controller_types:
            found_instances = list(filter(lambda inst: controller_type is inst, controller_memory))
            if len(found_instances) == 1:
                controller_instance = found_instances[0]
            elif len(found_instances) == 0:
                controller_instance = controller_type()
                controller_instance._set_logger(bot.logger)
                controller_memory.append(controller_instance)
            else:
                raise Exception('Invalid algorithm')
            controllers_to_add.append(controller_instance)

        bot.controllers = controllers_to_add


def _set_message_handlers(bots: list[Bot]) -> None:
    """
    Instantiate and set handlers
    """
    for bot in bots:
        if bot.message_handler_class is None:
            bot.message_handler_class = bot.view_class._default_message_handler_class
        bot.message_handler = bot.message_handler_class(bot.controllers, bot.logger)


def _instantiate_in_bots(bots: list[Bot]) -> None:
    """
    Instantiate and set to the bot instances, each controller must be singleton
    """
    _set_views(bots)
    _set_controllers(bots)
    _set_message_handlers(bots)
