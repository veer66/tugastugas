import datetime
from typing import Any, TypedDict, List
from sqlalchemy import String, Integer, Boolean, Date
from sqlalchemy import text
from sqlalchemy import Table
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import false
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from tugastugas.database import Base
from sqlalchemy.orm import relationship


class User(Base):
    """
    This is a User model that represents a user in the database. The
    fields `id`, `username`, and `password_hash` are all defined as
    Mapped columns, which provide SQLAlchemy's object-relational
    mapping functionality. 
    """

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(128), unique=True)
    password_hash: Mapped[str] = mapped_column(String(128))


#    tasks:Mapped[List["Task"]] = relationship(foreign_keys=["task.creator_id"])


class Task(Base):
    """
    Task model
    """

    __tablename__ = "task"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[String] = mapped_column(String())
    description: Mapped[String] = mapped_column(String(), default="")
    due_date: Mapped[str] = mapped_column(Date(), nullable=True)
    status: Mapped[String] = mapped_column(String(64))
    creator_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    creator: Mapped["User"] = relationship(foreign_keys=[creator_id])
    last_modifier_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    last_modifier: Mapped["User"] = relationship(
        foreign_keys=[last_modifier_id])
    from_undo: Mapped[bool] = mapped_column(Boolean,
                                            server_default=false())


# Adapted from cxↄ's comment on Stackoverflow https://stackoverflow.com/a/66453481/4685140


class HTask(Base):
    __tablename__ = 'h_task'
    id: Mapped[int] = mapped_column(primary_key=True)
    target_row_id: Mapped[int] = mapped_column(String(), nullable=False)
    executed_operation: Mapped[int] = mapped_column(Integer(), nullable=False)
    operation_executed_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        nullable=False,
        server_default=text('now()'))
    data_after_executed_operation: Mapped[dict] = mapped_column(JSONB,
                                                                nullable=True)
    from_undo: Mapped[bool] = mapped_column(Boolean)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship()
    used: Mapped[bool] = mapped_column(Boolean, server_default=false())
