"""FastAPI application with User authentication and GraphQL endpoint.

This application demonstrates user authentication using OAuth2 and integrates
a GraphQL endpoint for data access.

**Features:**

* User model with ID, username, and authentication status.
* OAuth2 authentication with fake token generation for demonstration.
* User retrieval based on access token and scope validation.
* Basic GraphQL endpoint with a context providing database session and user information.
* Authentication middleware using Bearer token and custom backend.
* Guard middleware to restrict unauthorized requests (example).

**Note:** This is a simplified example for demonstration purposes. Real-world
applications should implement secure password hashing and proper authentication mechanisms.
"""

from typing import Annotated, Any
from fastapi import Depends, FastAPI, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from tugastugas.schema import schema
from tugastugas.database import bind
from starlette.responses import PlainTextResponse
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.routing import Route
from starlette_graphene3 import GraphQLApp
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
)

from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware

app = FastAPI()

################ User schema #############


class User(BaseModel):
    """Represents a user entity with basic information.

    This model defines the attributes for a user:

    * `id`: The user's unique identifier (integer).
    * `username`: The user's login name (string).
    * `is_authenticated` (optional): A flag indicating if the user is currently authenticated (boolean).
    """
    id: int
    username: str
    is_authenticated: bool | None = None


################ OAUTH2 ##################

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def fake_decode_token(token):
    """Fakes token decoding for demonstration purposes (replace with real implementation).

      This function simulates token decoding by checking for predefined token strings. 
      It returns a dictionary with user information (ID, username, is_authenticated)
      if the token matches a valid string (access-token-1, access-token-2, or access-token-3).
      Otherwise, it returns None.

      **Important:** This function is for demonstration only. In a real application,
      you should implement a secure token decoding mechanism using a proper JWT library
      and secret key to verify and extract user information from a real access token.
      """
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


############# GraghQL #################

session = bind()


class BearerAuthBackend(AuthenticationBackend):
    """Custom authentication backend for Bearer token scheme.

      This backend checks for Bearer token authorization in the request headers.
      It extracts the token and uses `fake_decode_token` (for demonstration purposes)
      to decode it. If the token is valid, it returns user credentials and the User object.
      If the token is invalid or not found, it returns None.

      **Important:** This backend uses `fake_decode_token` which is for demonstration only.
      In a real application, you should implement a secure token decoding mechanism
      using a JWT library and secret key to verify real access tokens.
      """

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
    """Middleware to restrict access to unauthorized requests.

      This middleware checks if a user object is present in the request scope (`scope`)
      and if the user's `is_authenticated` attribute is True. If both conditions are met,
      it allows the request to proceed through the application (`await self.app(scope, receive, send)`).
      Otherwise, it returns a `PlainTextResponse` with a 401 Unauthorized status code
      effectively blocking the request.
      """

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
