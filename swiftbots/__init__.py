from swiftbots.bots_application import BotsApplication
from swiftbots.types import ILoggerFactory


def initialize_app(logger_factory: ILoggerFactory = None) -> BotsApplication:
    bot_app = BotsApplication(logger_factory)
    return bot_app
