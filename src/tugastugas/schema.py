"""
GraphQL schema
"""

import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType
from graphene_sqlalchemy.fields import SQLAlchemyConnectionField
from tugastugas.models import Project
from tugastugas.database import Base

class ProjectNode(SQLAlchemyObjectType):
    class Meta:
        model = Project
        interfaces = (relay.Node,)

class Query(graphene.ObjectType):
    node = relay.Node.Field()
    projects = graphene.List(ProjectNode)

    def resolve_projects(self, info):
        query = ProjectNode.get_query(info)
        return query.all()

# from tugastugas.database import bind


schema = graphene.Schema(query=Query)

#######################################
query = '''
  query Hey {
    projects {
      id,
      title
    }
  }
'''
from tugastugas.database import bind
bind()
result = schema.execute(query)

print(result)
