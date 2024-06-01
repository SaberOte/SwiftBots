__all__ = [
    'AppContainer'
]

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiftbots.all_types import ILogger, IScheduler
    from swiftbots.bots import Bot


class AppContainer:
    def __init__(self, bots: list['Bot'], logger: ILogger, scheduler: IScheduler) -> None:
        self.bots = bots
        self.logger = logger
        self.scheduler = scheduler
