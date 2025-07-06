import datetime
from typing import Annotated

from sqlalchemy import DateTime, SmallInteger, Integer, String, create_engine, Table, Column, MetaData, ForeignKey, text
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from fastapi import Depends


# metadata = MetaData()

# sync_eng = create_engine(
#   url='sqlite:///./db.sqlite3',
#   echo=True,
#   pool_size=5,
#   max_overflow=10,
# )

engine = create_async_engine(
  url='sqlite+aiosqlite:///db.sqlite3',
  echo=True,
  pool_size=5,
  max_overflow=10,
  # connect_args={"check_same_thread": False},
)
# db_session = async_sessionmaker(db, expire_on_commit=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
# session = sessionmaker(sync_eng, expire_on_commit=False)


async def get_session():
  async with async_session() as session:
    yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


str_3 = Annotated[str, 3]
str_16 = Annotated[str, 16]

class Base(DeclarativeBase):
  type_annotation_map = {
    str_3: String(3),
    str_16: String(16),
  }

# Base = declarative_base()

pk = Annotated[int, mapped_column(primary_key=True)]
# created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]
created_at = Annotated[datetime.datetime, mapped_column(
  default=datetime.datetime.utcnow,
  # server_default=text('CURRENT_TIMESTAMP'),
)]
updated_at = Annotated[datetime.datetime, mapped_column(
  default=datetime.datetime.utcnow,
  onupdate=datetime.datetime.utcnow,
  # server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
)]

class Session(Base):
  __tablename__ = 'foto_session'

  id: Mapped[pk]
  created: Mapped[created_at]
  updated: Mapped[updated_at]
  deleted: Mapped[datetime.datetime | None]
  year: Mapped[int] = mapped_column(SmallInteger)
  name: Mapped[str]
  pricelist_id: Mapped[int]


class Album(Base):
  __tablename__ = 'foto_album'

  id: Mapped[pk]
  created: Mapped[created_at]
  updated: Mapped[updated_at]
  deleted: Mapped[datetime.datetime | None]
  closed: Mapped[datetime.datetime | None]
  session_id: Mapped[int] = mapped_column(ForeignKey("foto_session.id", ondelete="CASCADE"))
  sh: Mapped[str] = mapped_column(String(3))
  shyear: Mapped[int] = mapped_column(SmallInteger)
  group: Mapped[str] = mapped_column(String(16))




# albumTable = Table(
#   "foto_album",
#   metadata,
#   Column("id", Integer, primary_key=True),
#   Column("session_id", Integer),
#   Column("sh", String),
#   Column("shyear", SmallInteger),
#   Column("group", String),
#   Column("created", DateTime),
#   Column("updated", DateTime),
#   Column("deleted", DateTime),
#   Column("closed", DateTime),
# )

# def init_db():
#   # metadata.drop_all(sync_eng)
#   metadata.create_all(sync_eng)


async def setup_database():
  async with engine.begin() as conn:
    # await conn.run_sync(Base.metadata.drop_all)
    await conn.run_sync(Base.metadata.create_all)

