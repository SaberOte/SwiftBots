from swiftbots.types import IView, IController, IMessageHandler, ILogger, IBasicMessageHandler


class Bot:
    """A storage of controllers and views"""

    name: str

    view_type: type[IView]
    controller_types: list[type[IController]]
    message_handler_type: type[IMessageHandler]

    view: IView
    controllers: list[IController]
    message_handler: IMessageHandler
    logger: ILogger

    def __init__(self, view_type: type[IView], controller_types: list[type[IController]],
                 message_handler_type: type[IMessageHandler], logger: ILogger, name: str):
        self.view_type = view_type
        self.controller_types = controller_types
        self.message_handler_type = message_handler_type
        self.logger = logger
        self.name = name


def _set_views(bots: list[Bot]) -> None:
    """
    Instantiate and set views
    """
    for bot in bots:
        bot.view = bot.view_type()


def _set_controllers(bots: list[Bot]) -> None:
    """
    Instantiate and set to the bot controllers, each one must be singleton
    """
    controller_memory: list[IController] = []
    for bot in bots:
        controllers_to_add: list[IController] = []
        controller_types = bot.controller_types

        for controller_type in controller_types:
            found_instances = list(filter(lambda inst: controller_type is inst, controller_memory))
            if len(found_instances) == 1:
                controller_instance = found_instances[0]
            elif len(found_instances) == 0:
                controller_instance = controller_type()
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
        bot.message_handler = bot.message_handler_type(bot.controllers, bot.logger)


def _instantiate_in_bots(bots: list[Bot]) -> None:
    """
    Instantiate and set to the bot instances, each controller must be singleton
    """
    _set_views(bots)
    _set_controllers(bots)
    _set_message_handlers(bots)
