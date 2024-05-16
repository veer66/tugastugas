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
def prepare(alembic_runner: Any) -> None:
    alembic_runner.migrate_up_to("head", return_current=False)

def test_project_query(pg_engine: Any) -> None:
    session_factory = sessionmaker(autocommit=False, autoflush=False,
                                   bind=pg_engine)
    pg_session = scoped_session_factory(session_factory)
    Base.query = pg_session.query_property()

    mut_query = '''
      mutation {
        createProject(
          title: "A1",
            content: {
              boards: [{name: "DOING", tasks: {body: "eat"}}]
            }
        ) { project { id } }
      }
    '''
    mut_result = schema.schema.execute(mut_query, context = {"session": pg_session})

    assert mut_result.errors is None

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
    added_id = str(mut_result.data["createProject"]["project"]["id"])
    del_query = 'mutation { deleteProject(id: ' + added_id + ') { id } }'
    del_result = mut_result = schema.schema.execute(del_query, context = {"session": pg_session})

    assert del_result.errors is None

    query_after_del = '''
              query {
                projects { id }
              }
              '''
    result_after_del = schema.schema.execute(query_after_del)
    assert len(result_after_del.data['projects']) == 0
