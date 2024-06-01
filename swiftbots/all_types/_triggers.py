from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional


class ITrigger(ABC):
    ...


class IPeriodTrigger(ITrigger, ABC):
    hours: Optional[float]
    minutes: Optional[float]
    seconds: Optional[float]

    @abstractmethod
    def __init__(self,
                 hours: Optional[float] = None,
                 minutes: Optional[float] = None,
                 seconds: Optional[float] = None
                 ):
        """
        :param hours: how many hours period. It will add to other parameters.
        :param minutes: how many minutes period. It will add to other parameters.
        :param seconds: how many seconds period. It will add to other parameters.
        """
        ...

    @abstractmethod
    def get_period(self) -> timedelta:
        ...
