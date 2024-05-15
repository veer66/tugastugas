from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column


class Base(DeclarativeBase):
    """
    This is the base class for all database models. It inherits from
    DeclarativeBase, which provides a convenient way to define SQLAlchemy
    models. The models defined using this class will automatically be
    registered with the database session and can be accessed through the
    Session object.
    """
    pass


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
