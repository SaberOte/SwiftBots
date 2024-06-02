__all__ = [
    'task',
    'TaskInfo'
]

from collections.abc import Callable
from typing import List, Union

from swiftbots.all_types import DecoratedCallable, ITrigger


class TaskInfo:
    def __init__(self,
                 name: str,
                 func: DecoratedCallable,
                 triggers: List[ITrigger],
                 run_at_start: bool):
        self.name = name
        self.func = func
        self.triggers = triggers
        self.run_at_start = run_at_start


def task(
    name: str,
    triggers: Union[ITrigger, List[ITrigger]],
    run_at_start: bool = False
) -> Callable[[DecoratedCallable], TaskInfo]:
    """
    Mark a controller method as a task.
    Depends on trigger(s), will be executed by scheduler.
    """
    assert isinstance(triggers, ITrigger) or isinstance(triggers, list), \
        'Trigger must be the type of ITrigger or a list of ITriggers'
    for trigger in triggers:
        assert isinstance(trigger, ITrigger), 'Triggers must be the type of ITrigger'
    assert isinstance(triggers, ITrigger) or len(triggers) > 0, 'Empty list of triggers'

    def wrapper(func: DecoratedCallable) -> TaskInfo:
        task_info = TaskInfo(name=name,
                             func=func,
                             triggers=triggers if isinstance(triggers, list) else [triggers],
                             run_at_start=run_at_start)
        return task_info
    return wrapper
