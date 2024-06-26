from abc import ABC
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from swiftbots.all_types import IDatabaseConnectionProvider


class AbstractDatabaseConnectionProvider(IDatabaseConnectionProvider, ABC):
    __db_session_maker: Optional[async_sessionmaker[AsyncSession]] = None

    @property
    def async_db_session_maker(self) -> async_sessionmaker[AsyncSession]:
        assert (
            self.__db_session_maker
        ), "Application hasn't database engine. Call use_database for application before running"
        return self.__db_session_maker

    def _set_db_session_maker(
        self, db_session_maker: Optional[async_sessionmaker[AsyncSession]]
    ) -> None:
        self.__db_session_maker = db_session_maker
