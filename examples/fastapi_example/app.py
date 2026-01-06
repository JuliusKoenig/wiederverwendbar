from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route

from wiederverwendbar.fastapi.root.app import RootApp
from wiederverwendbar.logger import LoggerSingleton
from wiederverwendbar.uvicorn import UvicornServer

from examples.fastapi_example.settings import settings
from examples.fastapi_example.api import api

LoggerSingleton(name=__name__, settings=settings.logger, init=True)  # ToDo fix this unresolved attr

html = """<!DOCTYPE html>
<html>
<head>
    <title>FastAPI Example</title>
</head>
<body>
    <h1>Welcome to the FastAPI Example Application!</h1>
    <p>This is a simple example of a FastAPI application with mounted Starlette apps.</p>
    <a href="/">Go to Root and test auto redirect.</a><br>
    <a href="/ui">Go to UI.</a><br>
    <a href="/api">Go to API.</a><br
</body>
</html>
"""

ui = Starlette(
    routes=[
        Route(
            "/",
            lambda r: HTMLResponse(html),
        ),
    ],
)

app = RootApp(settings=settings.root)

app.mount(path="/ui", app=ui, name="ui")
app.mount(path="/api", app=api, name="api")


@app.get("/test")
async def test_endpoint():
    return {"message": "Test endpoint is working!"}


if __name__ == "__main__":
    UvicornServer(app, settings=settings.server)
