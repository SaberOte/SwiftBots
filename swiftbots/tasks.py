from abc import ABC
from traceback import format_exc
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from swiftbots.types import ILogger, ITask

if TYPE_CHECKING:
    from swiftbots.bots import Bot


class Task(ITask, ABC):

    __db_session_maker = async_sessionmaker[AsyncSession] | None
    logger: ILogger

    def init(self, logger: ILogger, db_session_maker: async_sessionmaker[AsyncSession] | None) -> None:
        self.logger = logger
        self.__db_session_maker = db_session_maker

    @property
    def async_db_session_maker(self) -> async_sessionmaker[AsyncSession]:
        """
        Receive one async Database session to make transactions.
        Using is like:
        ```
        async with self.async_db_session_maker() as session:
            session.add(some_other_object)
            session.commit()
        ```
        Must be used in only 1 task or thread.
        """
        assert self.__db_session_maker, \
            "Application hasn't database engine. Call use_database for application before running"
        return self.__db_session_maker

    async def soft_close_async(self) -> None:
        pass


async def close_tasks_in_bots_async(bots: list['Bot']):
    tasks = set()
    for bot in bots:
        if bot.tasks:
            tasks.update(bot.tasks)
    for task in tasks:
        try:
            await task.soft_close_async()
        except Exception as e:
            await bots[0].logger.error_async(
                f'Raised an exception `{e}` when a view closing method called:\n{format_exc()}')

