from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

from swiftbots.all_types import ITrigger

if TYPE_CHECKING:
    from swiftbots.all_types import IController


class IScheduler(ABC):
    @abstractmethod
    def add_task(self, name: str,
                 triggers: list[ITrigger],
                 ) -> None:
        """Schedule task. To start execution, the method `start` must be called"""
        ...

    @abstractmethod
    def remove_task(self, name: str) -> None:
        """Unschedule task by name. This task will no longer be executed"""
        ...

    @abstractmethod
    async def start(self) -> None:
        """This method must be called to start scheduling tasks"""
        ...
