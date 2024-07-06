__all__ = [
    'SimpleScheduler'
]

import asyncio
import datetime
from collections.abc import Callable
from typing import Any, Dict, List, Optional

from swiftbots.all_types import IPeriodTrigger, IScheduler
from swiftbots.tasks.tasks import TaskInfo


def now() -> datetime.datetime:
    return datetime.datetime.now()


class TaskContainer:
    __last_called: Optional[datetime.datetime] = None
    __called_once = False

    def __init__(self,
                 task_info: TaskInfo,
                 caller: Callable,
                 start_point: datetime.datetime):
        self.caller: Callable[..., Any] = caller
        self.name = task_info.name
        self.triggers = task_info.triggers
        self.run_at_start = task_info.run_at_start
        self.start_point = start_point

    def set_called(self) -> None:
        self.__last_called = now()
        self.__called_once = True

    def should_run(self) -> bool:
        if not self.__called_once and self.run_at_start:
            return True

        left_point = self.__last_called if self.__last_called else self.start_point

        for trigger in self.triggers:
            if isinstance(trigger, IPeriodTrigger):
                if now() - left_point >= trigger.get_period():
                    return True
        return False


class SimpleScheduler(IScheduler):
    __tasks: Dict[str, TaskContainer]
    __ping_updates_period_seconds: float = 1.0
    __supported_trigger_types = (IPeriodTrigger,)

    def __init__(self):
        self.__tasks = {}

    def add_task(self,
                 task_info: TaskInfo,
                 caller: Callable[[], Any]
                 ) -> None:
        assert task_info.name not in self.__tasks, f'Task {task_info.name} has already been added'
        for trigger in task_info.triggers:
            assert isinstance(trigger, self.__supported_trigger_types), \
                f'Trigger type {trigger.__class__.__name__} is not supported'

        self.__tasks[task_info.name] = TaskContainer(task_info, caller, now())

    def remove_task(self, name: str) -> None:
        assert name in self.__tasks, f'Task {name} has not been added'
        del self.__tasks[name]

    async def start(self) -> None:
        await asyncio.sleep(0)
        while True:
            await self.__run_pending_tasks()
            await asyncio.sleep(self.__ping_updates_period_seconds)

    def __find_tasks_to_run(self) -> List[TaskContainer]:
        return [task for task in self.__tasks.values() if task.should_run()]

    async def __run_pending_tasks(self) -> None:
        for task in self.__find_tasks_to_run():
            # TODO: a temporary solution. Had better launch with `create_task`,
            #  but then class must supervise these tasks
            await task.caller()
            task.set_called()
            await asyncio.sleep(0)
