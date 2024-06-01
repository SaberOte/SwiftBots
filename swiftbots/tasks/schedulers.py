from swiftbots.all_types import IScheduler, ITrigger


class SimpleScheduler(IScheduler):


    def add_task(self, name: str, triggers: list[ITrigger]) -> None:


    def remove_task(self, name: str) -> None:
        pass

    async def start(self) -> None:
        pass