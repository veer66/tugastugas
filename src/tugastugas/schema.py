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
from graphene import Date
from graphene import Field
from graphene import Mutation
from graphene import Int
from graphene_sqlalchemy import SQLAlchemyObjectType
from graphene_sqlalchemy.fields import SQLAlchemyConnectionField
from graphene_sqlalchemy.types import ORMField
from graphene_sqlalchemy.utils import get_session
from graphql_relay import from_global_id
from sqlalchemy import select, delete, and_
from sqlalchemy.orm import aliased
from tugastugas.models import User, Task


class TaskNode(SQLAlchemyObjectType):
    "Graphene Project wrapper"

    class Meta:
        model = Task

    id = ORMField(type_=Int)
    creator = Field(String)
    last_modifier = Field(String)

    def resolve_creator(self, info):
        return self.creator.username

    def resolve_last_modifier(self, info):
        return self.last_modifier.username


class Query(graphene.ObjectType):
    "The main query object for Graphene"
    tasks = graphene.List(TaskNode,
                          status=String(),
                          creator=String(),
                          last_modifier=String(),
                          due_since=Date(),
                          due_before=Date())

    def resolve_tasks(self, info: Any, **kwargs) -> Any:
        session = get_session(info.context)
        user_id = info.context.get('user').id
        if user_id is None:
            raise GraphQLError('This op needs user-id.')
        proj_query = TaskNode.get_query(info)
        if 'status' in kwargs:
            proj_query = proj_query.filter_by(status=kwargs['status'])
        if 'creator' in kwargs:
            creator_alias = aliased(User)
            proj_query = proj_query.join(
                creator_alias, creator_alias.id == Task.creator_id).where(
                    creator_alias.username == kwargs['creator'])
        if 'last_modifier' in kwargs:
            last_modifier_alias = aliased(User)
            proj_query = proj_query.join(
                last_modifier_alias,
                last_modifier_alias.id == Task.last_modifier_id).where(
                    last_modifier_alias.username == kwargs['last_modifier'])
        if 'due_since' in kwargs:
            proj_query = proj_query.where(Task.due_date >= kwargs['due_since'])
        if 'due_before' in kwargs:
            proj_query = proj_query.where(Task.due_date < kwargs['due_before'])
        return proj_query.all()


#################### MUTATION ########################


def get_user(session, user_id):
    stmt = select(User).filter_by(id=user_id)
    user = session.scalars(stmt).one_or_none()
    return user


class CreateTask(Mutation):

    class Arguments:
        title = String(required=True)
        description = String(default_value="")
        due_date = Date()
        status = String(required=True)

    task = Field(TaskNode)

    def mutate(self,
               info,
               title,
               description="",
               due_date=None,
               status="pending"):
        session = get_session(info.context)
        user_id = info.context.get('user').id
        if user_id is None:
            raise GraphQLError('This op needs user-id.')
        user = get_user(session, user_id)
        if user is None:
            raise GraphQLError(f'The user-id {user_id} is not found.')
        new_task = Task(title=title,
                        description=description,
                        status=status,
                        due_date=due_date,
                        creator=user,
                        last_modifier=user)
        session.add(new_task)
        session.commit()
        return CreateTask(task=new_task)


def is_owned(a_task, user_id):
    return a_task.creator_id == user_id


def get_task(session, task_id):
    stmt = select(Task).filter_by(id=1)
    print(f'STMT = {stmt}')
    the_task = session.execute(stmt).scalar_one_or_none()
    return the_task


class DeleteTask(Mutation):

    class Arguments:
        id = String(required=True)

    id = String(required=True)

    def mutate(self, info, id):
        session = get_session(info.context)
        user_id = info.context.get('user').id
        if user_id is None:
            raise GraphQLError('This op needs user-id.')
        the_task = get_task(session, id)
        if the_task is None:
            raise GraphQLError(f'The task #{id} does not exist.')
        if not is_owned(the_task, user_id):
            raise GraphQLError('This project is not belong to the user.')
        del_stmt = delete(Task).where(Task.id == id).returning(Task.id)
        del_result = session.execute(del_stmt).one_or_none()
        if del_result is None:
            raise GraphQLError(f'Cannot delete the project #{id}')
        session.commit()
        return DeleteTask(id=id)


class UpdateTask(Mutation):

    class Arguments:
        id = Int(required=True)
        title = String(required=False)
        description = String(required=False)
        due_date = Date(required=False)
        status = String(required=False)

    task = Field(TaskNode)

    #title, description, due_date, status
    def mutate(self, info, id, **kwargs):
        session = get_session(info.context)
        user_id = info.context.get('user').id
        if user_id is None:
            raise GraphQLError('This op needs user-id.')
        the_task = get_task(session, id)
        if the_task is None:
            raise GraphQLError(f'The task #{id} does not exist.')
        for k in kwargs:
            v = kwargs[k]
            setattr(the_task, k, v)
        the_task.last_modifier_id = user_id
        session.add(the_task)
        session.commit()
        return UpdateTask(the_task)


class Mutation(ObjectType):
    create_task = CreateTask.Field()
    delete_task = DeleteTask.Field()
    update_task = UpdateTask.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
