from typing import Annotated

import uvicorn

from fastapi import Depends

from wiederverwendbar.branding import BrandingSettings
from wiederverwendbar.fastapi import FastAPISettings, FastAPI, get_app
from wiederverwendbar import __author__, __author_email__, __license__, __license_url__, __terms_of_service__
from wiederverwendbar.logger import LoggerSettings, LogLevels, LoggerSingleton

from examples import TEST_ICO
from examples.fastapi_example.router import router
from wiederverwendbar.printable_settings import PrintableSettings


class MySettings(PrintableSettings):
    branding: BrandingSettings
    logger: LoggerSettings
    api: FastAPISettings


settings = MySettings(branding=BrandingSettings(title="Test App",
                                                description="Test Description",
                                                version="0.1.0",
                                                author=__author__,
                                                author_email=__author_email__,
                                                license=__license__,
                                                license_url=__license_url__,
                                                terms_of_service=__terms_of_service__),
                      logger=LoggerSettings(log_level=LogLevels.DEBUG),
                      api=FastAPISettings(docs_favicon=TEST_ICO))

LoggerSingleton(name=__name__, settings=settings.logger, init=True)  # ToDo fix this unresolved attr


class MyApi(FastAPI):
    test_attr = "test_app_attr"


app = MyApi(api_settings=settings.api,
            branding_settings=settings.branding,
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


app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
