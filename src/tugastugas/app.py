from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel


class User(BaseModel):
    username: str
    disabled: bool | None = None


app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/")
def read_root():
    return {"Hello": "World"}


def fake_decode_token(token):
    if token == "access-token-1":
        return {"username": "user1", "disabled": False}
    elif token == "access-token-2":
        return {"username": "user2", "disabled": False}
    elif token == "access-token-3":
        return {"username": "user3", "disabled": False}
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
    current_user: Annotated[User, Security(get_current_user, scopes=["me"])],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    return {"access_token": "access-token-1", "token_type": "bearer"}


@app.get("/users/me/", response_model=User)
def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@app.get("/users/me/items/")
def read_own_items(
    current_user: Annotated[User, Security(get_current_active_user, scopes=["items"])],
):
    return [{"item_id": "Foo", "owner": current_user.username}]
