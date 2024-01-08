from swiftbots.all_types import ILoggerFactory
from swiftbots.bots_application import BotsApplication


def initialize_app(logger_factory: ILoggerFactory | None = None) -> BotsApplication:
    bot_app = BotsApplication(logger_factory)
    return bot_app
