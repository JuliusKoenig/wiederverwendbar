import inspect
from functools import wraps
from typing import Annotated, Callable, Any

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from wiederverwendbar.functions.is_coroutine_function import is_coroutine_function

# security = HTTPBasic()


class Api(FastAPI):
    def __init__(self, **kwargs):
        self._init = False
        self._original_add_api_route = None
        super().__init__(**kwargs)

    def __getattribute__(self, item):
        # to ensure router is not used before init
        if item == "router" and not self._init:
            raise RuntimeError("Class is not initialized!")
        return super().__getattribute__(item)

    def _protected_add_api_route(self, path: str, endpoint: Callable[..., Any], *args, **kwargs):
        # protected_flag = getattr(endpoint, "_protected", False)
        # if protected_flag:
        #     endpoint_signature = inspect.signature(endpoint)
        #     endpoint_signature_parameters = list(endpoint_signature.parameters.values())
        #     endpoint_signature_parameters.append(inspect.Parameter(name="credentials",
        #                                                            kind=inspect.Parameter.KEYWORD_ONLY,
        #                                                            annotation=Annotated[str, Depends(self.auth)]))
        #     endpoint.__signature__ = endpoint_signature.replace(parameters=endpoint_signature_parameters)
        return self._original_add_api_route(path, endpoint, *args, **kwargs)


    def setup(self) -> None:
        self._init = True

        # overwrite add_api_route for router
        self._original_add_api_route: Any = self.router.add_api_route
        self.router.add_api_route = self._protected_add_api_route

        super().setup()

    # def auth(self, credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Incorrect username or password",
    #         headers={"WWW-Authenticate": "Basic"},
    #     )



def protected(auth: bool = True):
    def decorator(func):
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


app = Api()


# _: Annotated[str, Depends(app.auth)]
# request: Request

def get_app(request: Request):
    print()


@app.get("/")
async def get_root(a=Depends(get_app)):
    return {"root": "root"}

@app.get("/sync")
# @protected()
def get_sync(qwe: str = "qwe"):
    return {"sync": qwe}


@app.get("/async")
# @protected()
def get_async(qwe: str = "qwe"):
    return {"async": qwe}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
