import uvicorn

from fastapi import APIRouter

from examples import TEST_ICO
from wiederverwendbar.fastapi import FastAPISettings, FastAPI
from wiederverwendbar import __author__, __author_email__, __license__, __license_url__, __terms_of_service__

settings = FastAPISettings(branding_title="Test App",
                           branding_description="Test Description",
                           branding_version="0.1.0",
                           branding_author=__author__,
                           branding_author_email=__author_email__,
                           branding_license=__license__,
                           branding_license_url=__license_url__,
                           branding_terms_of_service=__terms_of_service__,
                           api_docs_favicon=TEST_ICO)
app = FastAPI(settings=settings,
              separate_input_output_schemas=True)


@app.get("/test1")
def test1_get():
    return {"test1": "test1"}


@app.get("/test2")
def test2_get():
    return {"test2": "test2"}


router = APIRouter(prefix="/test3")


@router.get("/sub1")
def test3_sub1_get():
    return {"test3_sub1": "test3_sub1"}


app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
