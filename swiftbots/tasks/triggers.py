import asyncio
from typing import Optional

from swiftbots.all_types import ITrigger, IPeriodTrigger


class PeriodTrigger(IPeriodTrigger):

    def __init__(self,
                 hours: Optional[float] = None,
                 minutes: Optional[float] = None,
                 seconds: Optional[float] = None,
                 run_at_start: bool = False
                 ):
        pass
