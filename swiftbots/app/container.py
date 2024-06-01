__all__ = [
    'AppContainer'
]

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from swiftbots.all_types import ILogger, IScheduler
    from swiftbots.bots import Bot


class AppContainer:
    def __init__(self, bots: List['Bot'], logger: 'ILogger', scheduler: 'IScheduler') -> None:
        self.bots = bots
        self.logger = logger
        self.scheduler = scheduler
