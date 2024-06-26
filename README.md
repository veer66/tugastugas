# Tugastugas

Tugastugas is a showcase task manager.

A showcase for:

* GraphQL
* Graphene
* PostgreSQL
* SQLAlchemy
* Alembic
* FastAPI


## Objective

* Showing off what I'm capable of in web-backend.
* Updating my skills and knowledge in unfamiliar (for me) technologies, e.g., GraphQL, FastAPI.
* Refreshing my knowledge about new versions of tools, e.g., SQLAlchemy 2.x.

## Design Rationale

* I'm avoiding SQL 2011 temporal functionality in this project because using the temporal_tables extension isn't feasible with Amazon Aurora.
* "The implementation leverages [PL/pgSQL for undo operations](alembic/versions/fce4251eee5b_add_undo_function.py), as the support for JSON queries within the ORM is uncertain.
* Undoing function is based on restoring the latest version before the current one is made. However, a task can be modified by many users. This undoing function may need to be tuned for the case where a user wants to undo a change made by another user, depending on project requirements. 
* Since this project is not in production yet, using a candidate release version of graphene-sqlalchemy makes sense. Maintaining compatibility with the legacy version wouldn't be beneficial in this case. Additionally, migrating from the RC1 (release candidate 1) to the final release version should require less effort compared to migrating from a legacy version.
* Task sorting must be crucial for practical usage, but it is out of this project scope.

## Running for development

### Prerequisite

1. Docker
2. Bash

### Create Docker network

```
docker network create tugas-net
```

### Run PostgreSQL

```
docker run \
       --name tugas-dev-db \
	   --net tugas-net \
       -e POSTGRES_PASSWORD=tugas \
       -e POSTGRES_USER=tugas \
       -e POSTGRES_PASSWORD=tugas \
       -d docker.io/postgres:15
```

### Install Python packages


```
docker run --rm \
       -it \
       -u $UID \
       -v $(pwd):/work \
       -w /work \
       --net tugas-net \
       -e HOME=/work \
       -e DB_USER=tugas \
       -e DB_PASSWORD=tugas \
       -e DB_HOST=tugas-dev-db \
       -e DB_NAME=tugas \
       docker.io/python:3.11-bookworm \
       bash -c 'pip install -e .'
```

Note: If Docker on your operating system doesn't work well with the 
-u $UID option, you can safely remove that line. However, this has a side effect: the owner of newly created or modified files within the container will be the default Docker user.  Despite this, it should be acceptable for code evaluation purposes.

### Migrate database and add fake users

```
docker run --rm \
       -it \
       -u $UID \
       -v $(pwd):/work \
       -w /work \
       --net tugas-net \
       -e HOME=/work \
       -e DB_USER=tugas \
       -e DB_PASSWORD=tugas \
       -e DB_HOST=tugas-dev-db \
       -e DB_NAME=tugas \
       docker.io/python:3.11-bookworm \
       bash -c 'export PATH=/work/.local/bin:$PATH; alembic upgrade heads; python -m tugastugas.add_fake_users'
```

### Run FastAPI server

```
docker run --rm \
	   --name tugas-py \
       -it \
       -u $UID \
       -v $(pwd):/work \
       -w /work \
       --net tugas-net \
       -e HOME=/work \
       -e DB_USER=tugas \
       -e DB_PASSWORD=tugas \
       -e DB_HOST=tugas-dev-db \
       -e DB_NAME=tugas \
       docker.io/python:3.11-bookworm \
       bash -c 'export PATH=/work/.local/bin:$PATH; fastapi dev --host 0.0.0.0 src/tugastugas/app.py'
```

### Browse Tugastugas API

The command below should obtain an IP address, e.g., 172.18.0.3
```
docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' tugas-py
```

Then a web browser should be able to browse the URL http://172.18.0.3:8000/docs (Please replace 172.18.0.3 with an IP Address obtained from docker inspect).

## Usage examples

The following examples are accessing GraphAPI API via cURL command line. 
However, using a graphical client, e.g. [Altair](https://altairgraphql.dev/) is much more convenient.

For developing without full user management system, Tugastugas provides 3 fake access tokens, as follow:

1. access-token-1 for the user - usr1
2. access-token-2 for the user - usr2
3. access-token-3 for the user - usr3

One of them has to be put in HTTP header for authentication and identify the user. For example:

```
Authorization: Bearer access-token-1
```

### Create a task

* Query

```GraphQL
mutation {
  createTask(
        title:"Create a Mastodon instance",
        description:"For experimenting decentralize social network",
        status:"DOING",
        dueDate: "2027-01-01"
 ) { task { id } }
}
```
* Query via cURL

```Bash
curl 'http://172.18.0.3:8000/' \
     -X POST \
     -H 'Accept: application/json' \
     -H 'Content-Type: application/json' \
     -H 'Authorization: Bearer access-token-1' \
     --data-raw '{"query":"mutation {\n  createTask(\n        title:\"Create a Mastodon instance\",\n        description:\"For experimenting decentralize social network\",\n        status:\"DOING\",\n        dueDate: \"2027-01-01\"\n ) { task { id } }\n}","variables":{},"operationName":null}'
```


### Update a task

```GraphQL
mutation {
  updateTask(
        id:1,
        status:"DONE",
 ) { task { id } }
}
```


### Retrieve tasks

* Query

```GraphQL
query {
    tasks {
      id, title, description, status, dueDate, creator, lastModifier
    }
}
```

* Query via cURL

(Please replace 172.18.0.3 with your container's IP Address)

```Shell
curl 'http://172.18.0.3:8000/' \
	-X POST \
	-H 'Accept: application/json' \
	-H 'Content-Type: application/json' \
	-H 'Authorization: Bearer access-token-1' \
	--data-raw '{"query":"query Q1 {\n    tasks {\n      id, title, description, status, dueDate, creator, lastModifier\n    }\n}","variables":{},"operationName":"Q1"}'
```

### Filter tasks

These filters can be mixed in the same query.

1. Filter by ID

```GraphQL
query {
  tasks(id:1) {
    id,
    title,
    status
  }
}
```

2. Filter by status

```GraphQL
query {
  tasks(status:"DONE") {
    id,
  }
}
```

3. Filter by creator

```GraphQL
query  {
  tasks(creator:"usr2") {
    title,
  }
}
```

4. Filter by last modifer

```GraphQL
query {
  tasks(lastModifier:"usr2") {
    title,
  }
}
```

5. Filter by due before

```GraphQL
query {
  tasks(dueBefore:"2027-01-01") {
    title,
  }
}
```
6. Filter by due since

```GraphQL
query {
  tasks(dueSince:"2027-01-01") {
    title,
  }
}
```

### Delete a task

```GraphQL
mutation {
  deleteTask(id:1) { id }
}
```

### Undo

This mutation undo latest action of the current user inferred from the access token.

```GraphQL
mutation {
  undoTask { task { id } }
}
```

## Test

Testing can be run via pytest,
but fortunately, since it uses Docker to spin up a PostgreSQL instance for testing, it cannot be run from inside another Docker container.
