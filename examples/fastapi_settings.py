import uvicorn

from examples import TEST_ICO
from wiederverwendbar.fastapi.settings import FastAPISettings
from wiederverwendbar.fastapi.app import FastAPI
from fastapi import APIRouter

settings = FastAPISettings(api_title="test_app",
                           api_summary="Test summary",
                           api_description="Test description",
                           api_docs_favicon=TEST_ICO)
app = FastAPI(settings=settings)


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
