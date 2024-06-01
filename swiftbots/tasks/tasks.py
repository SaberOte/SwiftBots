__all__ = [
    'task',
    'run_every'
]

from swiftbots.all_types import ITrigger

from typing import Optional
from typing_extensions import Doc, Annotated


class Trigger:
    timer_seconds: Optional[float] = None
    schedule: Optional


def task(
    name: Annotated[str, Doc("Name of the task. Will manage task by its name")],
    scheduler: Trigger
):
    pass


def run_periodically(
    hours: Optional[float] = None,
    minutes: Optional[float] = None,
    seconds: Optional[float] = None,
    run_at_start: bool = False
) -> Trigger:
    assert hours >= 0 and minutes >= 0 and seconds >= 0, 'Time for scheduler must be positive or zero'



