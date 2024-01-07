from abc import ABC
from traceback import format_exc
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from swiftbots.abstract_classes import (
    AbstractAsyncHttpClientProvider,
    AbstractDatabaseConnectionProvider,
    AbstractLoggerProvider,
    AbstractSoftClosable,
)
from swiftbots.all_types import ILogger, ITask

if TYPE_CHECKING:
    from swiftbots.bots import Bot


class Task(ITask, AbstractDatabaseConnectionProvider, AbstractLoggerProvider, AbstractAsyncHttpClientProvider,
           AbstractSoftClosable, ABC):

    __db_session_maker = async_sessionmaker[AsyncSession] | None

    def init(self, logger: ILogger, db_session_maker: async_sessionmaker[AsyncSession] | None,
             name: str) -> None:
        self._set_logger(logger)
        self._set_db_session_maker(db_session_maker)
        if name:
            self.name = name


async def soft_close_tasks_in_bots_async(bots: list['Bot']) -> None:
    tasks = set()
    for bot in bots:
        if bot.tasks:
            tasks.update(bot.tasks)
    for task in tasks:
        try:
            await task._soft_close_async()
        except Exception as e:
            await task.logger.error_async(
                f'Raised an exception `{e}` when a view closing method called:\n{format_exc()}')
