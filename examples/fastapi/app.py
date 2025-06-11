from typing import Annotated

import uvicorn

from fastapi import Depends

from wiederverwendbar.fastapi import FastAPISettings, FastAPI, protected, get_app, HttpBasicAuthScheme, OAuth2PasswordBearerScheme
from wiederverwendbar import __author__, __author_email__, __license__, __license_url__, __terms_of_service__
from wiederverwendbar.logger import LoggerSettings, LogLevels, LoggerSingleton

from examples import TEST_ICO
from examples.fastapi.router import router


class MySettings(LoggerSettings, FastAPISettings):
    ...


settings = MySettings(branding_title="Test App",
                      branding_description="Test Description",
                      branding_version="0.1.0",
                      branding_author=__author__,
                      branding_author_email=__author_email__,
                      branding_license=__license__,
                      branding_license_url=__license_url__,
                      branding_terms_of_service=__terms_of_service__,
                      log_level=LogLevels.DEBUG,
                      api_docs_favicon=TEST_ICO,
                      api_auth_scheme=OAuth2PasswordBearerScheme())

LoggerSingleton(name=__name__, settings=settings, init=True)  # ToDo fix this unresolved attr


class MyApi(FastAPI):
    test_attr = "test_app_attr"


app = MyApi(settings=settings,
            separate_input_output_schemas=True)


@app.get("/sync")
def get_sync(_app: Annotated["MyApi", Depends(get_app)], query_param: str = "test_query_param"):
    return {"sync": {
        "test_query_param": query_param,
        "test_app_attr": _app.test_attr
    }}


@app.get("/async")
def get_async(_app: Annotated["MyApi", Depends(get_app)], query_param: str = "test_query_param"):
    return {"async": {
        "test_query_param": query_param,
        "test_app_attr": _app.test_attr
    }}


@app.get("/protected/sync")
@protected()
def get_sync(_app: Annotated["MyApi", Depends(get_app)], query_param: str = "test_query_param"):
    return {"protected_sync": {
        "test_query_param": query_param,
        "test_app_attr": _app.test_attr
    }}


@app.get("/protected/async")
@protected()
def get_async(_app: Annotated["MyApi", Depends(get_app)], query_param: str = "test_query_param"):
    return {"protected_async": {
        "test_query_param": query_param,
        "test_app_attr": _app.test_attr
    }}


app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
