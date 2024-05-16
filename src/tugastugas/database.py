import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session as scoped_session_factory
from sqlalchemy.orm import DeclarativeBase


def get_url():
    return "postgresql+psycopg://%s:%s@%s:%s/%s" % (
        os.getenv("DB_USER", "tugastugas"),
        os.getenv("DB_PASSWORD", "tugastugas"),
        os.getenv("DB_HOST", "localhost"),
        os.getenv("DB_PORT", "5432"),
        os.getenv("DB_NAME", "tugastugas"),
    )

class Base(DeclarativeBase):
    pass

def bind():
    engine = create_engine(get_url())
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    scoped_session = scoped_session_factory(session_factory)
    Base.query = scoped_session.query_property()
#    Base.query = scoped_session.query()
    Base.metadata.bind = engine
    return scoped_session

def init_db():
    session = scoped_session()

