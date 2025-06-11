from enum import Enum
from typing import Any, Optional

from fastapi import HTTPException, status
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from pydantic import Field
from starlette.requests import Request

from wiederverwendbar.fastapi.auth.schemes.base import BaseAuthScheme


class HttpBasicAuthScheme(BaseAuthScheme):
    class Type(str, Enum):
        HTTP_BASIC_AUTH = "http_basic_auth"

    type: Type = Field(default=Type.HTTP_BASIC_AUTH, title="Auth Type", description="The type of the auth.")
    realm: Optional[str] = Field(default=None, title="HTTP Basic authentication realm", description="")

    def __auth_data_dependency__(self) -> Any:
        return HTTPBasic(scheme_name=self.scheme_name,
                         realm=self.realm,
                         description=self.description,
                         auto_error=self.auto_error)

    async def __auth__(self, data: HTTPBasicCredentials, request: Request) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    __login__ = __auth__
