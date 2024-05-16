# Tugastugas

Tugastugas is a task-board backend inspired by Trello.

A showcase for:

* GraphQL
* Graphene
* SQLAlchemy
* PostgreSQL


## Objective

* Showing off what I'm capable of in web-backend.
* Updating my skills and knowledge in relatively new technologies, e.g., GraphQL.
* Refreshing my knowledge about new versions of tools, e.g., SQLAlchemy 2.x.

## Design Rationale

* Boards and tasks are stored in a JSONB column to avoid too many joins, which would degrade performance even with a few users.
* Project and user relations are stored in a traditional relational database table because querying projects would not cause as many join operations as joining projects with boards with tasks.
* I'm avoiding SQL 2011 temporal functionality in this project because using the temporal_tables extension isn't feasible with Amazon Aurora.
