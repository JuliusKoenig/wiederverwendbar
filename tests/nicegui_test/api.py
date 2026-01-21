from typing import Annotated

from fastapi import Depends

from wiederverwendbar.fastapi import ApiApp, get_app

from tests.nicegui_test.settings import settings
from tests.nicegui_test.router import router


class MyApi(ApiApp):
    test_attr = "test_app_attr"


api_app = MyApi(settings=settings.api,
            branding_settings=settings.branding,
            separate_input_output_schemas=True)


@api_app.get("/sync")
def get_sync(_app: Annotated["MyApi", Depends(get_app)], query_param: str = "test_query_param"):
    return {"sync": {
        "test_query_param": query_param,
        "test_app_attr": _app.test_attr
    }}


@api_app.get("/async")
def get_async(_app: Annotated["MyApi", Depends(get_app)], query_param: str = "test_query_param"):
    return {"async": {
        "test_query_param": query_param,
        "test_app_attr": _app.test_attr
    }}


api_app.include_router(router)
