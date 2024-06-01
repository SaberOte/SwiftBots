__all__ = [
    'task',
    'TaskInfo'
]

from typing import Optional, Union

from swiftbots.all_types import ITrigger


class TaskInfo:
    def __init__(self,
                 name: str,
                 triggers: list[ITrigger],
                 run_at_start: bool):
        self.name = name
        self.triggers = triggers
        self.run_at_start = run_at_start


def task(
    name: str,
    triggers: Union[ITrigger, list[ITrigger]],
    run_at_start: Optional[bool] = False
):
    """
    Mark a controller method as a task.
    Depends on trigger(s), will be executed by scheduler.
    """
    assert isinstance(triggers, ITrigger) or len(triggers) > 0, 'Empty list of triggers'
    return TaskInfo(name,
                    triggers if isinstance(triggers, list) else [triggers],
                    run_at_start)
