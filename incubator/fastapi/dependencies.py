from typing import Union, Any

from starlette.requests import Request

from wiederverwendbar.fastapi.app import FastAPI


async def get_app(request: Request) -> Union[FastAPI, Any]:
    if not isinstance(request.app, FastAPI):
        raise RuntimeError("The request app is not a FastAPI instance.")
    return request.app
