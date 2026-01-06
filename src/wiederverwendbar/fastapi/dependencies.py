from typing import Union, Any

from fastapi import FastAPI
from starlette.requests import Request


async def get_app(request: Request) -> Union[FastAPI, Any]:
    if not isinstance(request.app, FastAPI):
        raise RuntimeError("The request app is not a FastAPI instance.")
    return request.app
