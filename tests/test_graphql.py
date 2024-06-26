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
              title:"T1",
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
              title:"T2",
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


def create_task3(context):
    query = '''
        mutation C3 {
          createTask(
              title:"T3",
              description:"D3",
              dueDate: "2000-05-01",
              status:"DOING",
          ) { task { id } }
        }
    '''
    result = schema.schema.execute(query, context=context)
    assert result.errors is None


def create_tasks(context, context_user2):
    create_task1(context)
    create_task2(context)
    create_task3(context_user2)


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
    assert len(result.data['tasks']) == 3
    assert set([task['title']
                for task in result.data['tasks']]) == set(["T1", "T2", "T3"])


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
    assert len(result.data['tasks']) == 2


def update_task(context):
    query = '''
              mutation U1 {
                updateTask(
                  id:2
                  title:"T2-R1",
                  dueDate:"2027-01-01",
                  status:"DONE"
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
    assert result.data == {"updateTask": {"task": {"id": 2, "title": "T2-R1"}}}


def query_tasks_after_update_with_id_filter(context):
    query = '''
              query Q3 {
                tasks(id:2) {
                  id,
                  title,
                  status
                }
              }
            '''
    result = schema.schema.execute(query, context=context)
    assert result.errors is None
    assert result.data['tasks'][0] == {
        'id': 2,
        'title': 'T2-R1',
        'status': 'DONE'
    }


def query_tasks_with_status_eq_done(context):
    query = '''
              query QueryStatusEqDone {
                tasks(status:"DONE") {
                  id,
                }
              }
            '''
    result = schema.schema.execute(query, context=context)
    assert result.errors is None
    assert result.data['tasks'][0] == {'id': 2}


def query_tasks_with_creator_eq_usr2(context):
    query = '''
              query QueryStatusEqDone {
                tasks(creator:"usr2") {
                  title,
                }
              }
            '''
    result = schema.schema.execute(query, context=context)
    assert result.errors is None
    assert result.data['tasks'] == [{'title': 'T3'}]


def query_tasks_with_last_modifier_eq_usr2(context):
    query = '''
              query QueryStatusEqDone {
                tasks(lastModifier:"usr2") {
                  title,
                }
              }
            '''
    result = schema.schema.execute(query, context=context)
    assert result.errors is None
    assert set([task['title']
                for task in result.data['tasks']]) == set(['T2-R1', 'T3'])


def query_tasks_with_due_before(context):
    query = '''
              query QueryStatusEqDone {
                tasks(dueBefore:"2026-01-01") {
                  title,
                }
              }
            '''
    result = schema.schema.execute(query, context=context)
    assert result.errors is None
    assert result.data['tasks'] == [{'title': 'T3'}]


def query_tasks_with_due_since(context):
    query = '''
              query QueryStatusEqDone {
                tasks(dueBefore:"2026-01-01") {
                  title,
                }
              }
            '''
    result = schema.schema.execute(query, context=context)
    assert result.errors is None
    assert set([task['title']
                for task in result.data['tasks']]) == set(["T1", "T2-R1"])


def test_crud(pg_engine: Any) -> None:

    class TestUser(BaseModel):
        id: int

    user = TestUser(id=1)
    user2 = TestUser(id=2)
    session_factory = sessionmaker(autocommit=False,
                                   autoflush=False,
                                   bind=pg_engine)
    pg_session = scoped_session_factory(session_factory)
    Base.query = pg_session.query_property()
    context = {"session": pg_session, "user": user}
    context_user2 = {"session": pg_session, "user": user2}

    add_users(pg_session)
    create_tasks(context, context_user2)
    query_tasks(context)
    update_task(context)
    query_tasks_after_update_with_id_filter(context)
    query_tasks_with_status_eq_done(context)
    query_tasks_with_creator_eq_usr2(context)
    delete_task(context)
    query_tasks_after_delete(context)
