import datetime as dt

from swiftbots.tasks import Task


class MyTicker(Task):

    interval = dt.timedelta(seconds=10)
    name = 'ticker'

    async def tick(self):
        print(f"Time now: {dt.datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")
