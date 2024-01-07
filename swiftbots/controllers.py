from abc import ABC
from collections.abc import Sequence
from traceback import format_exc
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession

from swiftbots.types import IController

if TYPE_CHECKING:
    from swiftbots.bots import Bot


class Controller(IController, ABC):

    __db_session_maker = async_sessionmaker[AsyncSession] | None

    def init(self, db_session_maker: async_sessionmaker[AsyncSession] | None) -> None:
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


async def soft_close_controllers_in_bots_async(bots: Sequence['Bot']) -> None:
    """
    Close softly all controller's connections (like a database or http clients)
    """
    controllers = set()
    for bot in bots:
        controllers.update(bot.controllers)
    for controller in controllers:
        try:
            await controller.soft_close_async()
        except Exception as e:
            await bots[0].logger.error_async(
                f'Raised an exception `{e}` when a controller closing method called:\n{format_exc()}')
