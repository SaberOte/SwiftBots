import datetime as dt

from scheduler.base.timingtype import Weekday

from swiftbots.tasks import Task


class MyTicker(Task):

    START_AT: dt.datetime | Weekday | dt.timedelta | dt.time | None


    def __init__(self):
        self.counter = 1

    async def tick(self):
        print(f'Tick event: {self.counter}')
        self.counter += 1
