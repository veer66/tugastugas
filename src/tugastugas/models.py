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
    Basic task model
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
    from_undo: Mapped[bool] = mapped_column(Boolean, server_default=false())


# Adapted from cxↄ's comment on Stackoverflow https://stackoverflow.com/a/66453481/4685140


class HTask(Base):
    """Model for storing task history information.

      This SQLAlchemy model represents a table named 'h_task' that stores historical data 
      related to task operations. It keeps track of changes made to tasks, including:

      * `id` (int, primary key): Unique identifier for the history record.
      * `target_row_id` (int, not null): ID of the task object the operation was performed on.
      * `executed_operation 1-CREATE 2-DELETE 3-UPDATE
      * `operation_executed_at` (datetime, not null): Timestamp of when the operation was executed.
    * `data_after_executed_operation` is for storing the entire task row
      * `from_undo` (bool): Flag indicating if this record is a result of an undo operation.
      * `user_id` (int, foreign key): ID of the user who performed the operation (foreign key to user.id).
      * `user` (User, relationship): Relationship to the User model for retrieving user information.
      * `used` (bool, default=False): Flag indicating if this history record has been used 
      in an undo operation (defaults to False).

      This model is likely used to implement undo functionalities for tasks. 
    """
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
