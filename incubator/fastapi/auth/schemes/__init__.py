from typing import Union

from wiederverwendbar.fastapi.auth.schemes.base import (BaseAuthScheme, protected)

from wiederverwendbar.fastapi.auth.schemes.http_basic_auth import (HttpBasicAuthScheme)
from wiederverwendbar.fastapi.auth.schemes.oauth2_password_bearer import (OAuth2PasswordBearerScheme)

AVAILABLE_AUTH_SCHEMES = Union[
    None,
    HttpBasicAuthScheme,
    OAuth2PasswordBearerScheme
]
