# Tugastugas

Tugastugas is a showcase task manager.

A showcase for:

* GraphQL
* Graphene
* SQLAlchemy
* PostgreSQL


## Objective

* Showing off what I'm capable of in web-backend.
* Updating my skills and knowledge in unfamiliar (for me) technologies, e.g., GraphQL.
* Refreshing my knowledge about new versions of tools, e.g., SQLAlchemy 2.x.

## Design Rationale

* I'm avoiding SQL 2011 temporal functionality in this project because using the temporal_tables extension isn't feasible with Amazon Aurora.

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

### Retrieve tasks

* Query:

```GraphQL
query {
    tasks {
      id, title, description, status, dueDate, creator, lastModifier
    }
}
```

* Example using cURL

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

1. Filter by ID

```GraphQL
query {
  tasks(id:2) {
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
  tasks(dueBefore:"2026-01-01") {
    title,
  }
}
```
6. Filter by due since

```GraphQL
query {
  tasks(dueBefore:"2026-01-01") {
    title,
  }
}
```
### Create a task

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

### Update a task

```GraphQL
mutation {
  updateTask(
        id:1,
        status:"DONE",
 ) { task { id } }
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
