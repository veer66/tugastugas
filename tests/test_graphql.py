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
from tugastugas.models import Project, User
from tugastugas.models import Board, Task
from pydantic import BaseModel

alembic_engine: Any = create_postgres_fixture()
pg_engine = create_postgres_fixture(Base)




@pytest.mark.alembic()
def prepare(alembic_runner: Any) -> None:
    alembic_runner.migrate_up_to("head", return_current=False)

def test_project_query(pg_engine: Any) -> None:

    class TestUser(BaseModel):
        id: int

    user = TestUser(id=1)
    session_factory = sessionmaker(autocommit=False, autoflush=False,
                                   bind=pg_engine)
    pg_session = scoped_session_factory(session_factory)
    Base.query = pg_session.query_property()

    # Add a user
    pg_session.add(User(id=1, username='usr1', password_hash=''))
    pg_session.add(User(id=2, username='usr2', password_hash=''))

    pg_session.commit()

    context = {"session": pg_session, "user": user}

    mut_query = '''
      mutation {
        createProject(
          title: "A1",
            content: {
              boards: [{name: "DOING", tasks: [{body: "eat"}]}]
            }
        ) { project { id } }
      }
    '''
    mut_result = schema.schema.execute(mut_query, context=context)

    assert mut_result.errors is None
    added_id = str(mut_result.data["createProject"]["project"]["id"])

    query = '''
              query Hey {
                projects {
                  id,
                  title
                }
              }
            '''
    Base.query = pg_session.query_property()
    result = schema.schema.execute(query, context=context)
    assert result.data['projects'][0]['title'] == 'A1'


    update_query = '''
      mutation {
        updateProject(
          id: __ID__,
          title: "A2",
            content: {
              boards: [{name: "DONE", tasks: [{body: "eat"}, {body: "sleep"}]}]
            }
        ) { project { id, title, content { boards { name, tasks { body } } } } }
      }
    '''
    update_query = update_query.replace('__ID__', str(added_id))
    update_result = schema.schema.execute(update_query, context=context)

    assert update_result.errors is None

    board = update_result.data["updateProject"]["project"]["content"]["boards"][0]
    assert (board["tasks"][1]["body"]) == "sleep"

    after_update_query = '''
              query {
                projects {
                  id,
                  title,
                  content { boards { name, tasks { body } } }
                }
              }
            '''
    after_update_result = schema.schema.execute(after_update_query, context=context)

    assert after_update_result.errors is None

    another_user_query = 'query { projects { id } }'
    another_user_context = {"session": pg_session, "user": User(id=300)}
    another_user_result = schema.schema.execute(another_user_query, context=another_user_context)
    assert len(another_user_result.data['projects']) == 0

    after_update_project = after_update_result.data["projects"][0]
    after_update_board = after_update_project["content"]["boards"][0]
    assert after_update_board["tasks"][1]["body"] == "sleep"

    del_query = 'mutation { deleteProject(id: ' + added_id + ') { id } }'
    del_result = mut_result = schema.schema.execute(del_query, context=context)

    assert del_result.errors is None

    query_after_del = '''
              query {
                projects { id }
              }
              '''
    result_after_del = schema.schema.execute(query_after_del, context=context)
    assert len(result_after_del.data['projects']) == 0
