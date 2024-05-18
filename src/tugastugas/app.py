from typing import Annotated, Any
from fastapi import Depends, FastAPI, HTTPException, status, Security, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from tugastugas.schema import schema
from tugastugas.database import bind
from starlette.responses import PlainTextResponse
from starlette.requests import HTTPConnection, Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from starlette.routing import Route
from starlette_graphene3 import GraphQLApp

app = FastAPI()

################ User schema #############


class User(BaseModel):
    id: int
    username: str
    is_authenticated: bool | None = None


################ OAUTH2 ##################

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def fake_decode_token(token):
    if token == "access-token-1" or token == b"access-token-1":
        return {"id": 1, "username": "usr1", "is_authenticated": True}
    elif token == "access-token-2" or token == b"access-token-2":
        return {"id": 2, "username": "usr2", "is_authenticated": True}
    elif token == "access-token-3" or token == b"access-token-3":
        return {"id": 3, "username": "usr3", "is_authenticated": True}
    return None


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user_dict = fake_decode_token(token)
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = User(**user_dict)
    return user


def get_current_active_user(
    current_user: Annotated[User,
                            Security(get_current_user, scopes=["me"])], ):
    if not current_user.is_authenticated:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    return {"access_token": "access-token-1", "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)], ):
    return current_user


############# GraghQL #################

session = bind()

from starlette.authentication import (AuthCredentials, AuthenticationBackend,
                                      AuthenticationError)

from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware


class BearerAuthBackend(AuthenticationBackend):

    async def authenticate(self, conn):
        if "Authorization" not in conn.headers:
            return

        auth = conn.headers["Authorization"]
        scheme, token = auth.split()
        if scheme.lower() != 'bearer':
            return
        user_dict = fake_decode_token(token)
        if user_dict is None:
            return
        user = User(**user_dict)
        return AuthCredentials(["authenticated"]), user


class GuardUnauthorizedRequestMiddleware:

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive,
                       send: Send) -> None:
        if "user" in scope and scope["user"].is_authenticated:
            await self.app(scope, receive, send)
        else:
            response = PlainTextResponse("Unauthorized", status_code=401)
            await response(scope, receive, send)
            return


middleware = [
    Middleware(AuthenticationMiddleware, backend=BearerAuthBackend()),
    Middleware(GuardUnauthorizedRequestMiddleware)
]


async def get_context_value(request: HTTPConnection) -> Any:
    return {"session": session, "user": request.user}


graphql_app = GraphQLApp(schema, context_value=get_context_value)
graphql_route = Route('/',
                      endpoint=graphql_app,
                      middleware=middleware,
                      methods=["POST"])

app.add_route('/', graphql_route)
