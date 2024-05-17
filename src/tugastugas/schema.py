"""
GraphQL schema
"""
from typing import Any
from graphql import GraphQLError
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
from tugastugas.models import Project, UserProject, User
from sqlalchemy import select, delete, and_


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
        session = get_session(info.context)
        user_id = info.context.get('user').id
        if user_id is None:
            raise GraphQLError('This op needs user-id.')
        proj_query = ProjectNode.get_query(info).join(UserProject, UserProject.project_id == Project.id).filter_by(user_id=user_id)
        return proj_query.all()


#################### MUTATION ########################


class TaskInput(InputObjectType):
    body = String(required=True)


class BoardInput(InputObjectType):
    name = String(required=True)
    tasks = List(TaskInput)


class ProjectContentInput(InputObjectType):
    boards = List(BoardInput)


def get_user(session, user_id):
    stmt = select(User).filter_by(id=user_id)
    user = session.scalars(stmt).one_or_none()
    return user


class CreateProject(Mutation):
    class Arguments:
        title = String(required=True)
        content = ProjectContentInput(required=True)

    project = Field(ProjectNode)

    def mutate(self, info, title, content):
        session = get_session(info.context)
        user_id = info.context.get('user').id
        if user_id is None:
            raise GraphQLError('This op needs user-id.')
        user = get_user(session, user_id)
        if user is None:
            raise GraphQLError(f'The user-id {user_id} is not found.')
        project = Project(title=title, content=content)
        user_project = UserProject()
        user_project.project = project
        user_project.user = user
        session.add(project)
        session.add(user_project)
        session.commit()
        return CreateProject(project=project)


def is_owned(session, user_id, project_id):
    stmt = select(UserProject).filter_by(project_id=project_id, user_id=user_id)
    assoc = session.scalars(stmt).one_or_none()
    return assoc is not None

class DeleteProject(Mutation):
    class Arguments:
        id = Int(required=True)

    id = Int(required=True)

    def mutate(self, info, id):
        session = get_session(info.context)
        user_id = info.context.get('user').id
        if user_id is None:
            raise GraphQLError('This op needs user-id.')
        if not is_owned(session, user_id, id):
            raise GraphQLError('This project is not belong to the user.')
        del_stmt = delete(Project).where(Project.id == id).returning(Project.id)
        del_result = session.execute(del_stmt).one_or_none()
        if del_result is None:
            raise GraphQLError(f'Cannot delete the project #{id}')
        session.commit()
        return DeleteProject(id=id)


class UpdateProject(Mutation):
    class Arguments:
        id = Int(required=True)
        title = String(required=True)
        content = ProjectContentInput(required=True)

    project = Field(ProjectNode)

    def mutate(self, info, id, title, content):
        session = get_session(info.context)
        user_id = info.context.get('user').id
        if user_id is None:
            raise GraphQLError('This op needs user-id.')
        if not is_owned(session, user_id, id):
            raise GraphQLError('This project is not belong to the user.')
        stmt = select(Project).filter_by(id=id)
        the_project = session.execute(stmt).scalar_one_or_none()
        if the_project is None:
            raise GraphQLError(f'This project #{id} does not exist.')
        the_project.title = title
        the_project.content = content
        session.add(the_project)
        session.commit()
        return CreateProject(project=the_project)


class Mutation(ObjectType):
    create_project = CreateProject.Field()
    delete_project = DeleteProject.Field()
    update_project = UpdateProject.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
