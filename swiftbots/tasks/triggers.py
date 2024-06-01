from datetime import timedelta
from typing import Optional

from swiftbots.all_types import IPeriodTrigger


class PeriodTrigger(IPeriodTrigger):
    def __init__(self,
                 hours: Optional[float] = None,
                 minutes: Optional[float] = None,
                 seconds: Optional[float] = None
                 ):
        assert hours >= 0 and minutes >= 0 and seconds >= 0, 'Time for scheduler must be positive or zero'
        self.__period = timedelta(hours=hours, minutes=minutes, seconds=seconds)

    def get_period(self) -> timedelta:
        return self.__period
