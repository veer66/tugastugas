from typing import Any, TypedDict
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from tugastugas.database import Base


class User(Base):
    """
    This is a User model that represents a user in the database. The
    fields `id`, `username`, and `password_hash` are all defined as
    Mapped columns, which provide SQLAlchemy's object-relational
    mapping functionality. 
    """

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[String] = mapped_column(String(128), unique=True)
    password_hash: Mapped[String] = mapped_column(String(128))


class Task(TypedDict):
    body: str


class Board(TypedDict):
    name: str
    tasks: list[Task]


class ProjectData(TypedDict):
    boards: list[Board]


class Project(Base):
    """
    This is a Project model. It consists of the title, and data, which is mainly
    about boards.
    """

    __tablename__ = "project"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[String] = mapped_column(String())
    content: Mapped[ProjectData] = mapped_column(JSONB)
