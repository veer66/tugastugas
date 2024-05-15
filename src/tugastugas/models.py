from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
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
    username: Mapped[String] = mapped_column(String(128))
    password_hash: Mapped[String] = mapped_column(String(128))


class Project(Base):
    """
    This is a Project model. It consists of the title, and data, which is mainly
    about boards.
    """

    __tablename__ = "project"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[String] = mapped_column(String())
