import os

from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route

from wiederverwendbar.logger import LoggerSingleton, LoggerSettings
from wiederverwendbar.singleton import Singleton
from wiederverwendbar.uvicorn import UvicornServer

init = False
try:
    Singleton.get_by_type(LoggerSingleton)
    init = True
except RuntimeError:
    ...

if not init or __name__ == '__main__':
    LoggerSingleton(name="test", settings=LoggerSettings(log_level=LoggerSettings.LogLevels.DEBUG), init=True)

app = Starlette(
    routes=[
        Route(
            "/",
            lambda r: HTMLResponse('<h1>Hello, world!</h1>'),
        ),
    ],
)

if __name__ == '__main__':
    UvicornServer("uvicorn_server:app", host="0.0.0.0", port=8000, workers=1)
    print()
