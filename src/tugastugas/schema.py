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
from graphene import Int
from graphene_sqlalchemy import SQLAlchemyObjectType
from graphene_sqlalchemy.types import ORMField
from graphene_sqlalchemy.utils import get_session
from tugastugas.models import Project
from sqlalchemy import delete

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

    id = ORMField(type_=Int)
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


    def mutate(self, info, title, content):
        session = get_session(info.context)
        project = Project(title = title, content = content)
        session.add(project)
        session.commit()
        return CreateProject(project = project)


class DeleteProject(Mutation):
    class Arguments:
        id = Int(required=True)

    id = Int(required=True)

    def mutate(self, info, id):
        session = get_session(info.context)
        stmt = delete(Project).where(Project.id == id).returning(Project.id)
        del_result = session.execute(stmt).one_or_none()
        session.commit()
        return DeleteProject(id = id)


class Mutation(ObjectType):
    create_project = CreateProject.Field()
    delete_project = DeleteProject.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
