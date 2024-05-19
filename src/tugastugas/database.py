import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session as scoped_session_factory
from sqlalchemy.orm import DeclarativeBase


def get_url():
    """Constructs a connection URL for PostgreSQL database.

      This function retrieves environment variables for database credentials and connection details,
      and constructs a connection URL string suitable for connecting to a PostgreSQL database
      using the psycopg2 adapter.

      It uses the following environment variables (with defaults if not set):
      * DB_USER: Username for the database (defaults to "tugastugas").
      * DB_PASSWORD: Password for the database (defaults to "tugastugas").
      * DB_HOST: Hostname or IP address of the database server (defaults to "localhost").
      * DB_PORT: Port number of the database server (defaults to "5432").
      * DB_NAME: Name of the database to connect to (defaults to "tugastugas").

      Returns:
      str: The constructed connection URL string for PostgreSQL.
    """
    return "postgresql+psycopg://%s:%s@%s:%s/%s" % (
        os.getenv("DB_USER", "tugastugas"),
        os.getenv("DB_PASSWORD", "tugastugas"),
        os.getenv("DB_HOST", "localhost"),
        os.getenv("DB_PORT", "5432"),
        os.getenv("DB_NAME", "tugastugas"),
    )


class Base(DeclarativeBase):
    """Abstract base class for SQLAlchemy models.

      This class serves as a base class for all other SQLAlchemy models in the application.
      It inherits from `DeclarativeBase` provided by the `sqlalchemy.ext.declarative` module.
      By inheriting from this class, other model classes automatically gain some functionalities 
      like table name generation and relationship management.

      **Note:** This class itself is typically not instantiated directly.
    """
    pass


def bind():
    """Establishes a connection to the PostgreSQL database and configures SQLAlchemy session management.

      This function performs the following steps:
      1. Retrieves the database connection URL using the `get_url` function.
          (Replace '.get_url' with the actual import path if different)
      2. Prints the connection URL for informational purposes (consider logging instead in production).
      3. Creates a SQLAlchemy engine object using the retrieved connection URL.
          Disables echo mode to avoid logging SQL statements (can be enabled for debugging).
      4. Configures a session factory using the engine:
          - Disables autocommit mode (manual commit required for transactions).
          - Disables autoflush mode (improves performance for bulk operations).
      5. Creates a thread-local scoped session factory for efficient session management.
      6. Associates the `query` property of the `Base` class with the scoped session's query method.
      7. Binds the SQLAlchemy metadata to the engine.
      8. Returns the scoped session object for use with database operations.

      Returns:
      ScopedSession: A thread-local scoped session object for interacting with the database.
    """
    url = get_url()
    engine = create_engine(url, echo=False)
    session_factory = sessionmaker(autocommit=False,
                                   autoflush=False,
                                   bind=engine)
    scoped_session = scoped_session_factory(session_factory)
    Base.query = scoped_session.query_property()
    Base.metadata.bind = engine
    return scoped_session
