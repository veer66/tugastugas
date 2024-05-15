"""
GraphQL querying tests
"""
import pytest
from tugastugas import schema
from tugastugas.models import Project
from tugastugas.database import Base
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import text

alembic_engine = create_postgres_fixture()

def session_fn(session):
    session.add(Project(title='fake-proj-1'))
    session.flush()
    session.commit()

#pg_session = create_postgres_fixture(Base, session_fn, session=True)
pg_engine = create_postgres_fixture(Base)

@pytest.mark.alembic()
def test_project_query(alembic_runner, pg_engine):
    alembic_runner.migrate_up_to("head", return_current=False)

    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.orm import scoped_session as scoped_session_factory

    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)
    pg_session = scoped_session_factory(session_factory)
    Base.query = pg_session.query_property()

    pg_session.add(Project(title="A1"))
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
 


