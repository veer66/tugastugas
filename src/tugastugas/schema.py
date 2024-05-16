"""
GraphQL schema
"""
from typing import Any
import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType
from graphene_sqlalchemy.fields import SQLAlchemyConnectionField
from tugastugas.models import Project


class ProjectNode(SQLAlchemyObjectType):
    "Graphene Project wrapper"
    class Meta:
        "meta"
        model = Project
        interfaces = (relay.Node,)


class Query(graphene.ObjectType):
    "The main query object for Graphene"
    node = relay.Node.Field()
    projects = graphene.List(ProjectNode)

    def resolve_projects(self, info: Any) -> Any:
        proj_query = ProjectNode.get_query(info)
        return proj_query.all()


schema = graphene.Schema(query=Query)
