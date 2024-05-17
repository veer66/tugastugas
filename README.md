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
* Project-level syncing with clients eliminates the need for client-side ID mapping, compared to board- or task-level approaches.

## Usage examples

The following examples are accessing GraphAPI API via cURL command line. 
However, using a graphical client, e.g. [Altair](https://altairgraphql.dev/) is much more convenient.

### Retrieve projects

```
curl -H 'Accept: application/json' \
	 -H 'Content-type: application/json' \
	 -H 'Authorization: Bearer access-token-1' \
	 -d "{\"query\": \"query { projects { id } }\"}" \
	 -v \
	 http://localhost:8000/
```

### Create a project

```
curl -H 'Accept: application/json' \
	 -H 'Content-type: application/json' \
	 -H 'Authorization: Bearer access-token-1' \
	 -d "{\"query\": \"mutation { createProject(title:\\\"PRJ1\\\", content: {boards: [{name: \\\"DOING\\\", tasks: [{body: \\\"eat\\\"}]}]}) { project { id }}}\"}" \
	 -v \
	 http://localhost:8000/
```

### Update a project

```
curl -H 'Accept: application/json' \
	 -H 'Content-type: application/json' \
	 -H 'Authorization: Bearer access-token-1' \
	 -d "{\"query\": \"mutation { updateProject(id:9,title:\\\"X-PRJ1\\\", content: {boards: [{name: \\\"DOING\\\", tasks: {body: \\\"eat\\\"}}]}) { project { id }}}\"}" \
	 -v \
	 http://localhost:8000/
```

### Delete a project

```
curl -H 'Accept: application/json' \
	 -H 'Content-type: application/json' \
	 -H 'Authorization: Bearer access-token-1' \
	 -d "{\"query\": \"mutation { deleteProject(id:1) { id } }\"}" \
	 -v \
	 http://localhost:8000/
```
