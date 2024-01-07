"""From https://docs.sqlalchemy.org/en/20/orm/quickstart.html"""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Note(Base):

    __tablename__ = "note"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(25))
    text: Mapped[str] = mapped_column(String(4000))
    modified: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow())

    def __repr__(self) -> str:
        return f"Note(id={self.id!r}, name={self.name!r})"


# Base.registry.configure()
