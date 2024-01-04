from abc import ABC
from typing import Optional

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession

from swiftbots.types import IController


class Controller(IController, ABC):

    __db_session_maker = Optional[async_sessionmaker[AsyncSession]]

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
        assert self.__db_session_maker is not None, \
            "Application hasn't database engine. Call use_database for application before running"
        return self.__db_session_maker

    def init(self, db_session_maker: async_sessionmaker[AsyncSession]) -> None:
        self.__db_session_maker = db_session_maker
