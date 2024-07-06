__all__ = [
    'PeriodTrigger'
]


from datetime import timedelta

from swiftbots.all_types import IPeriodTrigger


class PeriodTrigger(IPeriodTrigger):
    def __init__(self,
                 hours: float = 0,
                 minutes: float = 0,
                 seconds: float = 0
                 ):
        assert hours >= 0 and minutes >= 0 and seconds >= 0, 'Time for scheduler must be positive or zero'
        self.__period = timedelta(hours=hours, minutes=minutes, seconds=seconds)

    def get_period(self) -> timedelta:
        return self.__period
