from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from swiftbots.tasks import TaskInfo


class IScheduler(ABC):
    @abstractmethod
    def add_task(self,
                 task_info: 'TaskInfo',
                 caller: Callable[[], Any]
                 ) -> None:
        """
        Add the task as a candidate for scheduling.
        """
        ...

    @abstractmethod
    def remove_task(self, name: str) -> None:
        """Unschedule task by name. This task won't be executed until `add_task` will be called"""
        ...

    @abstractmethod
    async def start(self) -> None:
        """
        The framework will call this method once, just when the app is started.
        All tasks will be scheduled and then executed here.
        The framework will make confidence that the appropriate controller method will
        be executed with demanded dependencies.
        """
        ...
