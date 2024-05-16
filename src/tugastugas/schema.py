"""
GraphQL schema
"""
from typing import Any
import graphene
from graphene import relay
from graphene import ObjectType, InputObjectType
from graphene import String
from graphene import List
from graphene import Field
from graphene import Mutation
from graphene_sqlalchemy import SQLAlchemyObjectType
from graphene_sqlalchemy.utils import get_session
from tugastugas.models import Project


class TaskNode(ObjectType):
    body = String()


class BoardNode(ObjectType):
    name = String()
    tasks = List(TaskNode)


class ProjectContentNode(ObjectType):
    boards = List(BoardNode)


class ProjectNode(SQLAlchemyObjectType):
    "Graphene Project wrapper"
    class Meta:
        "meta"
        model = Project
        interfaces = (relay.Node,)

    content = Field(ProjectContentNode)


class Query(graphene.ObjectType):
    "The main query object for Graphene"
    node = relay.Node.Field()
    projects = graphene.List(ProjectNode)

    def resolve_projects(self, info: Any) -> Any:
        proj_query = ProjectNode.get_query(info)
        return proj_query.all()


#################### MUTATION ########################


class TaskInput(InputObjectType):
    body = String(required=True)


class BoardInput(InputObjectType):
    name = String(required=True)
    tasks = List(TaskInput)


class ProjectContentInput(InputObjectType):
    boards = List(BoardInput)


class CreateProject(Mutation):
    class Arguments:
        title = String(required=True)
        content = ProjectContentInput(required=True)

    project = Field(ProjectNode)

    #@classmethod
    #def mutate(cls, root, info, title, content):
    def mutate(self, info, title, content):
        session = get_session(info.context)
        project = Project(title = title, content = content)
        session.add(project)
        session.commit()
        return CreateProject(project = project)


class Mutation(ObjectType):
    create_project = CreateProject.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
