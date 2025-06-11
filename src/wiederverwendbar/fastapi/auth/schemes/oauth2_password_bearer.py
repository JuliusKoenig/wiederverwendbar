from enum import Enum
from typing import Any, Annotated

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer as _OAuth2PasswordBearer
from pydantic import Field

from wiederverwendbar.fastapi.auth.schemes.base import BaseAuthScheme


class OAuth2PasswordBearerScheme(BaseAuthScheme):
    class Type(str, Enum):
        OAUTH2_PASSWORD_BEARER = "oauth2_password_bearer"

    type: Type = Field(default=Type.OAUTH2_PASSWORD_BEARER, title="Auth Type", description="The type of the auth.")
    token_url: str = Field(default="/login", title="Login URL", description="The login URL of the OAuth2.")

    def setup(self):
        # ensure the token_url starts with '/'
        self.token_url = self.token_url.rstrip("/")

        super().setup()

    def __routes__(self):
        super().__routes__()

        # add login route
        self.router.add_api_route(self.token_url, self.__login__, methods=["POST"])

    def __auth_data_dependency__(self) -> Any:
        return _OAuth2PasswordBearer(tokenUrl=self.prefix + self.token_url)

    async def __auth__(self, data: str) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    async def __login__(self, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
        # return {"access_token": user.username, "token_type": "bearer"}
