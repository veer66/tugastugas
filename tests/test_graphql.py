"""
GraphQL querying tests
"""
from typing import Any
import pytest
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session as scoped_session_factory
from tugastugas.database import Base
from tugastugas import schema
from tugastugas.models import Project
from tugastugas.models import Board, Task

alembic_engine: Any = create_postgres_fixture()
pg_engine = create_postgres_fixture(Base)


@pytest.mark.alembic()
def test_project_query(alembic_runner: Any, pg_engine: Any) -> None:
    alembic_runner.migrate_up_to("head", return_current=False)
    session_factory = sessionmaker(autocommit=False, autoflush=False,
                                   bind=pg_engine)
    pg_session = scoped_session_factory(session_factory)
    Base.query = pg_session.query_property()
    a_task: Task = {"body": "task1"}
    a_board: Board = {"name": "doing", "tasks": [a_task]}
    pg_session.add(Project(title="A1", data={"boards": [a_board]}))
    pg_session.commit()
    query = '''
              query Hey {
                projects {
                  id,
                  title
                }
              }
            '''
    Base.query = pg_session.query_property()
    result = schema.schema.execute(query)
    assert result.data['projects'][0]['title'] == 'A1'
