from wiederverwendbar.fastapi.root.app import RootApp
from wiederverwendbar.logger import LoggerSingleton
from wiederverwendbar.uvicorn import UvicornServer

from examples.fastapi_example.settings import settings
from examples.fastapi_example.api import api

LoggerSingleton(name=__name__, settings=settings.logger, init=True)  # ToDo fix this unresolved attr

app = RootApp(settings=settings.root)

app.mount(path="/api", app=api, name="api")


@app.get("/test")
async def test_endpoint():
    return {"message": "Test endpoint is working!"}


if __name__ == "__main__":
    UvicornServer(app, settings=settings.server)
