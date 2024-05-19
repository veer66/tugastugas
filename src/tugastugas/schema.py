"""
GraphQL schema
"""
from typing import Any
from graphql import GraphQLError
import graphene
from graphene import ObjectType
from graphene import String
from graphene import Date
from graphene import Field
from graphene import Mutation
from graphene import Int
from graphene import List
from graphene_sqlalchemy import SQLAlchemyObjectType
from graphene_sqlalchemy.types import ORMField
from graphene_sqlalchemy.utils import get_session
from sqlalchemy import select, delete, text
from sqlalchemy.orm import aliased
from tugastugas.models import User, Task


class TaskNode(SQLAlchemyObjectType):
    """Graphene representation of a Task model object.

    This class wraps the Task model from your application's database and defines
    fields for GraphQL queries. It inherits from `SQLAlchemyObjectType` provided by Graphene
    to leverage SQLAlchemy integration.

    These following fields are treated specially:
      
    * `id`: the ID field has to be forced its type to be integer to prevent generated ID.
    * `creator`: A field representing the username of the task creator (string).
    * `last_modifier`: A field representing the username of the last modifier (string).

    The class also defines resolver functions for `creator` and `last_modifier` fields.
    These resolvers access the corresponding username attributes from the related user objects
    associated with the task.
    """

    class Meta:
        model = Task

    id = ORMField(type_=Int)
    creator = Field(String)
    last_modifier = Field(String)

    def resolve_creator(self, info):
        return self.creator.username

    def resolve_last_modifier(self, info):
        return self.last_modifier.username


class Query(ObjectType):
    """Root query object for the GraphQL API.

      This class defines the main entry point for GraphQL queries. It provides a single
      field named `tasks` which returns a list of `TaskNode` objects.

      * `tasks` (List[TaskNode]): Retrieves a list of tasks based on provided filters.

      The `resolve_tasks` method handles the logic for retrieving tasks based on
      optional filter arguments. It leverages the `TaskNode` class for task representation
      and filters tasks based on:

      * `id`: Filter by task ID (integer).
      * `status`: Filter by task status (string).
      * `creator`: Filter by username of the task creator (string).
      * `last_modifier`: Filter by username of the last modifier (string).
      * `due_since`: Filter tasks due on or after a specific date (Date).
      * `due_before`: Filter tasks due before a specific date (Date).

      **Note:** This implementation requires a user to be authenticated (user_id in context)
      to access tasks. It raises a `GraphQLError` if user authentication is missing.
      """
    tasks = List(TaskNode,
                 id=Int(),
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
        if 'id' in kwargs:
            proj_query = proj_query.filter_by(id=kwargs['id'])
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
    """Mutation for creating a new Task object.

      This class defines a mutation named 'CreateTask' that allows users to create new tasks.
      It requires arguments for title, description (optional), due date (optional), and status.

      * Arguments:
      * `title` (String, required): The title of the new task.
      * `description` (String, optional): A description for the new task (default empty string).
      * `due_date` (Date, optional): The due date for the new task (can be null).
      * `status` (String, required): The initial status of the new task (required).

      * Returns:
      A `CreateTask` object with a single field:
      * `task` (TaskNode): The newly created task object.

      The `mutate` method handles the logic for creating a new task. It leverages the database
      session and user context information from `info`. It performs the following steps:

      1. Retrieves the user ID from the context (raises error if missing).
      2. Fetches the user object from the database based on the user ID.
      3. Creates a new `Task` object with provided arguments and associates it with the user.
      4. Adds the new task to the database session and commits the changes.
      5. Performs additional actions related to task history management 
      6. Returns a `CreateTask` object with the newly created task.

      **Note:** This implementation requires user authentication (user_id in context)
      to create tasks. It raises a `GraphQLError` if user authentication is missing.
      """

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
        history_stmt = text("""
          INSERT INTO h_task (target_row_id,
                    executed_operation,
                    data_after_executed_operation,
                    from_undo,
                    user_id)
          SELECT task.id,
            1,
            to_jsonb(task),
            task.from_undo,
            :user_id
          FROM task
          WHERE task.id = :task_id;
        """)
        session.execute(history_stmt, {
            "user_id": user_id,
            "task_id": new_task.id
        })
        session.commit()
        return CreateTask(task=new_task)


def is_owned(a_task, user_id):
    return a_task.creator_id == user_id


def get_task(session, task_id):
    stmt = select(Task).filter_by(id=task_id)
    the_task = session.execute(stmt).scalar_one_or_none()
    return the_task


class DeleteTask(Mutation):
    """Mutation for deleting a Task object.

      This class defines a mutation named 'DeleteTask' that allows users to delete tasks.
      It requires a single argument for the task ID.

      * Arguments:
      * `id` (Int, required): The ID of the task to be deleted.

      * Returns:
      A `DeleteTask` object with a single field:
      * `id` (Int): The ID of the deleted task.

      The `mutate` method handles the logic for deleting a task. It leverages the database
      session and user context information from `info`. It performs the following steps:

      1. Retrieves the user ID from the context (raises error if missing).
      2. Fetches the task object from the database based on the provided ID.
      3. Verifies that the task exists (raises error if not found).
      4. Checks if the user attempting to delete the task is the owner (raises error if not).
      5. Performs additional actions related to task history management.
      6. Deletes the task from the database using a SQLAlchemy delete query.
      7. Commits the changes to the database.
      8. Returns a `DeleteTask` object with the ID of the deleted task.

      **Note:** This implementation requires user authentication (user_id in context)
      to delete tasks. It also enforces ownership checks to ensure users can only delete
      tasks they created. It raises `GraphQLError` for various failure scenarios.
  """

    class Arguments:
        id = Int(required=True)

    id = Int(required=True)

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
        history_stmt = text("""
          INSERT INTO h_task (target_row_id,
                    executed_operation,
                    data_after_executed_operation,
                    from_undo,
                    user_id)
          SELECT task.id,
            2,
            to_jsonb(task),
            task.from_undo,
            :user_id
          FROM task
          WHERE task.id = :task_id;
        """)
        session.execute(history_stmt, {"user_id": user_id, "task_id": id})
        session.commit()

        del_stmt = delete(Task).where(Task.id == id).returning(Task.id)
        del_result = session.execute(del_stmt).one_or_none()
        if del_result is None:
            raise GraphQLError(f'Cannot delete the project #{id}')
        session.commit()
        return DeleteTask(id=id)


class UpdateTask(Mutation):
    """Mutation for updating a Task object.

      This class defines a mutation named 'UpdateTask' that allows users to update existing tasks.
      It requires a task ID (required) and accepts optional arguments for the fields to update.

      * Arguments:
      * `id` (Int, required): The ID of the task to be updated.
      * `title` (String, optional): The updated title for the task.
      * `description` (String, optional): The updated description for the task.
      * `due_date` (Date, optional): The updated due date for the task.
      * `status` (String, optional): The updated status for the task.

      * Returns:
      A `UpdateTask` object with a single field:
      * `task` (TaskNode): The updated task object.

      The `mutate` method handles the logic for updating a task. It leverages the database
      session and user context information from `info`. It performs the following steps:

      1. Retrieves the user ID from the context (raises error if missing).
      2. Fetches the task object from the database based on the provided ID.
      3. Verifies that the task exists (raises error if not found).
      4. Performs additional actions related to task history management 
      5. Iterates over provided keyword arguments (excluding `id`).
      6. For each argument, updates the corresponding attribute of the task object.
      7. Sets the `last_modifier_id` attribute of the task to the current user ID.
      8. Adds the updated task object to the database session.
      9. Commits the changes to the database.
      10. Returns a `UpdateTask` object with the updated task.

      **Note:** This implementation requires user authentication (user_id in context)
      to update tasks. It also raises a `GraphQLError` if the task with the provided ID is not found.
    """

    class Arguments:
        id = Int(required=True)
        title = String(required=False)
        description = String(required=False)
        due_date = Date(required=False)
        status = String(required=False)

    task = Field(TaskNode)

    def mutate(self, info, id, **kwargs):
        session = get_session(info.context)
        user_id = info.context.get('user').id
        if user_id is None:
            raise GraphQLError('This op needs user-id.')
        the_task = get_task(session, id)

        history_stmt = text("""
          INSERT INTO h_task (target_row_id,
                    executed_operation,
                    data_after_executed_operation,
                    from_undo,
                    user_id)
          SELECT task.id,
            3,
            to_jsonb(task),
            task.from_undo,
            :user_id
          FROM task
          WHERE task.id = :task_id;
        """)
        session.execute(history_stmt, {"user_id": user_id, "task_id": id})
        session.commit()

        if the_task is None:
            raise GraphQLError(f'The task #{id} does not exist.')
        for k in kwargs:
            v = kwargs[k]
            setattr(the_task, k, v)
        the_task.last_modifier_id = user_id
        session.add(the_task)
        session.commit()
        return UpdateTask(the_task)


class UndoTask(Mutation):
    """Mutation for undoing the latest task operation.

      This class defines a mutation named 'UndoTask' that allows users to undo the
      most recent operation performed on their tasks. It does not require any arguments.

      * Returns:
      A `UndoTask` object with a single field:
      * `task` (TaskNode, optional): The task object after the undo operation
        (may be None if the undo operation involved task creation).

      The `mutate` method handles the logic for undoing the latest task operation.
      It leverages the database session and user context information from `info`. 
      It performs the following steps:

      1. Retrieves the user ID from the context (raises error if missing).
      2. Perform undoing by querying PL/pgSQL function - undo_task_action
      3. Verifies that a valid undo record exists (raises error if not).
      4. Analyzes the operation type:
      - If type 1 (create task): cannot undo creation, return an empty `UpdateTask`.
      5. Fetches the task object from the database based on the retrieved task ID.
      8. Returns a `UndoTask` object if it is possible

      **Note:** This implementation requires user authentication (user_id in context)
      to undo tasks. It also performs basic validation to ensure undo operations 
      are possible. It raises `GraphQLError` for various failure scenarios 
      like missing authentication, missing undo record, or non-existent task.
      """

    class Arguments:
        pass

    task = Field(TaskNode)

    def mutate(self, info):
        session = get_session(info.context)
        user_id = info.context.get('user').id
        if user_id is None:
            raise GraphQLError('This op needs user-id.')

        undo_result = session.execute(
            text("SELECT undo_task_action(:user_id)"), {
                "user_id": user_id
            }).scalar_one_or_none()

        if undo_result is None or undo_result[0] is None:
            raise GraphQLError(f'Cannot undo anything for user {user_id}')
        op_type, task_id = undo_result
        if op_type == '1':
            return UpdateTask(task=None)
        session.commit()
        the_task = get_task(session, int(task_id))
        if the_task is None:
            raise GraphQLError(f'The task #{id} does not exist.')
        return UpdateTask(task=the_task)


class Mutation(ObjectType):
    """Root mutation type for the GraphQL API.

    This class groups together all mutation fields available in the API.
      It provides functionalities for managing tasks:

      * `create_task`: Creates a new task (see 'CreateTask' for details).
      * `delete_task`: Deletes an existing task (see 'DeleteTask' for details).
      * `update_task`: Updates an existing task (see 'UpdateTask' for details).
      * `undo_task`: Undoes the latest task operation (see 'UndoTask' for details).

      **Note:** All mutations require user authentication (user_id in context).
      Refer to the individual mutation classes for specific requirements and behaviors.
      """
    create_task = CreateTask.Field()
    delete_task = DeleteTask.Field()
    update_task = UpdateTask.Field()
    undo_task = UndoTask.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
