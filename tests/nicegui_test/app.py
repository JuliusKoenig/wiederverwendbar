from wiederverwendbar.fastapi.root.app import RootApp
from wiederverwendbar.logger import LoggerSingleton
from wiederverwendbar.uvicorn import UvicornServer

from tests.nicegui_test.settings import settings
from nicegui_test.ui import ui_app
from tests.nicegui_test.api import api_app

LoggerSingleton(name=__name__, settings=settings.logger, ignored_loggers_like="engineio.server",
                init=True)  # ToDo fix this unresolved attr

app = RootApp(settings=settings.root)

app.mount(path="/ui", app=ui_app, name="ui")
app.mount(path="/api", app=api_app, name="api")


@app.get("/test")
async def test_endpoint():
    return {"message": "Test endpoint is working!"}


if __name__ == "__main__":
    UvicornServer(app, settings=settings.server)
