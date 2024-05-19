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
from tugastugas.models import User, Task
from pydantic import BaseModel

alembic_engine: Any = create_postgres_fixture()
pg_engine = create_postgres_fixture(Base)


@pytest.mark.alembic()
def prepare(alembic_runner: Any) -> None:
    alembic_runner.migrate_up_to("head", return_current=False)


def add_users(pg_session):
    pg_session.add(User(id=1, username='usr1', password_hash=''))
    pg_session.add(User(id=2, username='usr2', password_hash=''))

    pg_session.commit()


def create_task1(context):
    query = '''
        mutation C1 {
          createTask(
              title:"TITLE1",
              description:"DESC1",
              dueDate:"2026-01-01",
              status:"DOING",
          )
          {
            task {
              id
            }
          }
        }
    '''
    result = schema.schema.execute(query, context=context)
    assert result.errors is None


def create_task2(context):
    query = '''
        mutation C2 {
          createTask(
              title:"TITLE2",
              description:"DESC2",
              status:"DOING",
          )
          {
            task {
              id
            }
          }
        }
    '''
    result = schema.schema.execute(query, context=context)
    assert result.errors is None


def create_tasks(context):
    create_task1(context)
    create_task2(context)


def query_tasks(context):
    query = '''
              query Q1 {
                tasks {
                  title
                }
              }
            '''
    result = schema.schema.execute(query, context=context)
    assert result.errors is None
    assert len(result.data['tasks']) == 2
    tasks = result.data['tasks']
    assert tasks[0]['title'] == 'TITLE1'
    assert tasks[1]['title'] == 'TITLE2'


def delete_task(context):
    query = '''
    mutation D1 {
      deleteTask(id:2) { id }
    }
    '''
    result = schema.schema.execute(query, context=context)
    assert result.errors is None
    assert result.data == {"deleteTask": {"id": 2}}


def query_tasks_after_delete(context):
    query = '''
              query Q1 {
                tasks {
                  title
                }
              }
            '''
    result = schema.schema.execute(query, context=context)
    assert result.errors is None
    assert len(result.data['tasks']) == 1


def update_task(context):
    query = '''
              mutation U1 {
                updateTask(
                  id:1
                  title:"T3"
                ) {
                  task {
                    id,
                    title
                  }
                }
              }
            '''
    result = schema.schema.execute(query, context=context)
    assert result.errors is None
    assert result.data == {"updateTask": {"task": {"id": 1, "title": "T3"}}}


def query_tasks_after_update(context):
    query = '''
              query Q3 {
                tasks {
                  id,
                  title
                }
              }
            '''
    result = schema.schema.execute(query, context=context)
    assert result.errors is None
    assert result.data['tasks'][0] == {'id': 1, 'title': 'T3'}


def test_crud(pg_engine: Any) -> None:

    class TestUser(BaseModel):
        id: int

    user = TestUser(id=1)
    session_factory = sessionmaker(autocommit=False,
                                   autoflush=False,
                                   bind=pg_engine)
    pg_session = scoped_session_factory(session_factory)
    Base.query = pg_session.query_property()
    context = {"session": pg_session, "user": user}

    add_users(pg_session)
    create_tasks(context)
    query_tasks(context)
    delete_task(context)
    query_tasks_after_delete(context)
    update_task(context)
    query_tasks_after_update(context)
