import inspect
from abc import ABC, abstractmethod
from enum import Enum
from functools import wraps
from typing import Any, Optional, Union, Annotated

from fastapi import Depends, APIRouter
from pydantic import BaseModel, PrivateAttr, Field

from wiederverwendbar.functions.is_coroutine_function import is_coroutine_function


class BaseAuthScheme(BaseModel, ABC):
    _router: Optional[APIRouter] = PrivateAttr(None)
    type: None = Field(default=None, title="Auth Type", description="The type of the auth.")
    prefix: str = Field(default="/auth", title="API prefix", description="The prefix for the API routes.")
    tags: Optional[list[Union[str, Enum]]] = Field(default=["auth"], title="Tags", description="The tags for the API routes.")
    name: Optional[str] = Field(default=None, title="Security scheme name", description="It will be included in the generated OpenAPI.")
    description: Optional[str] = Field(default=None, title="Security scheme description", description="It will be included in the generated OpenAPI.")
    auto_error: Optional[bool] = Field(default=True, title="Auto error", description="By default, if the authentication is not successful, the Auth scheme will automatically "
                                                                                     "cancel the request and send the client an error."
                                                                                     "\n"
                                                                                     "If `auto_error` is set to `False`, when the authentication requirements are not met, "
                                                                                     "instead of erroring out, the dependency result will be `None`."
                                                                                     "\n"
                                                                                     "This is useful when you want to have optional authentication."
                                                                                     "It is also useful when you want to have authentication that can be"
                                                                                     "provided in one of multiple optional ways.")

    def __call__(self):
        return self.__auth__

    @property
    def router(self) -> APIRouter:
        if self._router is None:
            raise RuntimeError(f"{self.__class__.__name__}.setup() must be called before accessing the router.")
        return self._router

    def model_post_init(self, context: Any, /) -> None:
        super().model_post_init(context)

        # check if type is set
        if self.type is None:
            raise RuntimeError(f"{self.__class__.__name__}.type is not set.")

        self.setup()

    def setup(self):
        # ensure the prefix starts with '/' or is ''
        if self.prefix != "":
            self.prefix = self.prefix.rstrip("/")

        # create api router
        self._router = APIRouter(prefix=self.prefix, tags=self.tags)

        # # backup original login method
        # original_login = self.__login__
        # original_login_signature = inspect.signature(original_auth)

        # create routes
        self.__routes__()

        # create auth data dependency
        auth_data_dependency = self.__auth_data_dependency__()
        if not callable(auth_data_dependency):
            raise RuntimeError(f"{self.__class__.__name__}.__auth_data_dependency__() method must return a callable.")

        # backup original auth method
        original_auth = self.__auth__
        original_auth_signature = inspect.signature(original_auth)

        async def __auth__(*args, **kwargs):
            bound_attr = original_auth_signature.bind(*args, **kwargs)
            return await original_auth(*bound_attr.args)

        # generate new auth method signature parameters
        auth_signature_parameters = []
        auth_param_overwritten = False
        for param in original_auth_signature.parameters.values():
            if param.name == "data":
                param = inspect.Parameter(name=param.name,
                                          kind=param.kind,
                                          annotation=Annotated[param.annotation, Depends(auth_data_dependency)])
                auth_param_overwritten = True
            auth_signature_parameters.append(param)
        if not auth_param_overwritten:
            raise RuntimeError(f"{self.__class__.__name__}.__auth__() method must have an auth parameter.")

        # overwrite auth method signature
        __auth__.__signature__ = original_auth_signature.replace(parameters=auth_signature_parameters)

        # overwrite auth method
        # noinspection PyAttributeOutsideInit
        self.__auth__ = __auth__

    def __routes__(self):
        ...

    @abstractmethod
    def __auth_data_dependency__(self) -> Any:
        ...

    @abstractmethod
    async def __auth__(self, *args) -> dict[str, Any]:
        ...

    @abstractmethod
    async def __login__(self, *args) -> dict[str, Any]:
        ...

    # @classmethod
    # async def compare(cls, validate_str: str, correct_str: str) -> bool:
    #     validate_str_bytes = validate_str.encode("utf8")
    #     correct_str_bytes = correct_str.encode("utf8")
    #     return secrets.compare_digest(validate_str_bytes, correct_str_bytes)


def protected(auth: bool = True):
    """Protect an api route with authentication."""

    def decorator(func):
        if hasattr(func, '_protected'):
            raise RuntimeError(f"Function '{func.__name__}' is already protected.")

        # wrap function
        if is_coroutine_function(func):
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
        else:
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

        # update wrap function signature
        wraps(func)(wrapper)

        # set auth flag
        wrapper._protected = auth

        return wrapper

    return decorator
