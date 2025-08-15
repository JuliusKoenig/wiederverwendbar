from typing import Annotated, TYPE_CHECKING

from fastapi import APIRouter, Depends

from wiederverwendbar.fastapi import protected, get_app

if TYPE_CHECKING:
    from examples.fastapi.app import MyApi

router = APIRouter(prefix="/sub")


@router.get("/sync")
def get_sync(_app: Annotated["MyApi", Depends(get_app)], query_param: str = "test_query_param"):
    return {"sync": {
        "test_query_param": query_param,
        "test_app_attr": _app.test_attr
    }}


@router.get("/async")
def get_async(_app: Annotated["MyApi", Depends(get_app)], query_param: str = "test_query_param"):
    return {"async": {
        "test_query_param": query_param,
        "test_app_attr": _app.test_attr
    }}


@router.get("/protected/sync")
@protected()
def get_sync(_app: Annotated["MyApi", Depends(get_app)], query_param: str = "test_query_param"):
    return {"protected_sync": {
        "test_query_param": query_param,
        "test_app_attr": _app.test_attr
    }}


@router.get("/protected/async")
@protected()
def get_async(_app: Annotated["MyApi", Depends(get_app)], query_param: str = "test_query_param"):
    return {"protected_async": {
        "test_query_param": query_param,
        "test_app_attr": _app.test_attr
    }}
