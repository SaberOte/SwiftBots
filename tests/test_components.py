import asyncio
import inspect
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Annotated, Any, List, Tuple

from swiftbots import PeriodTrigger, depends, task
from swiftbots.functions import DependencyContainer, resolve_function_args
from swiftbots.tasks import SimpleScheduler, TaskInfo
from swiftbots.types import AnnotatedType

logs: List[Tuple[str, timedelta]] = []
start_time_point: datetime


def compute_delta(now: datetime) -> timedelta:
    return now - start_time_point


@task('logger1', PeriodTrigger(seconds=2.0), run_at_start=False)
async def logger1(logger_num: str, delta: Annotated[timedelta, depends(compute_delta)]):
    await asyncio.sleep(0)
    logs.append((logger_num, delta))


class Test:
    # @pytest.mark.timeout(3)
    def test_simple_scheduler(self):
        global start_time_point
        start_time_point = datetime.now()
        sched = SimpleScheduler()

        task_info = logger1
        args = {'logger_num': '1'}
        def caller():
            task_info.func('1')
        sched.add_task(logger1, logger1.func)

    def test_dependency_injection(self):
        def dep2(s2: int):
            return s2 ** 3

        def dep1(s1: int, d2: Annotated[int, depends(dep2)]):
            return s1 ** 2, d2

        def caller(c: int, d1: Annotated[int, depends(dep1)]):
            return c, *d1

        data = {'s2': 5, 's1': 32, 'c': 12}
        args = resolve_function_args(caller, data)
        assert caller(**args) == (12, 32 ** 2, 5 ** 3)
