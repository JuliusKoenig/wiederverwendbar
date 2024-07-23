import logging
import asyncio
from typing import Sequence, Optional

import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_400_BAD_REQUEST
from starlette_admin import RequestAction
from starlette_admin.base import BaseAdmin
from starlette_admin.contrib.mongoengine import Admin, ModelView
from starlette_admin.actions import action
from starlette_admin.exceptions import ActionFailed
from starlette_admin.helpers import not_none
from nicegui import ui
from mongoengine import connect, Document, StringField

logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)

# connect to database
connect("test",
        host="localhost",
        port=27017)

# Create starlette app
app = Starlette(
    routes=[
        Route(
            "/",
            lambda r: HTMLResponse("<a href=" / admin / ">Click me to get to Admin!</a>"),
        ),
    ],
)


class ActionLogger(logging.Logger):
    class ActionLoggerHandler(logging.Handler):
        def __init__(self, nicegui_linear_progress: ui.linear_progress, nicegui_log: ui.log, step: int, close_callback: Optional[callable] = None):
            super().__init__()
            self.linear_progress = nicegui_linear_progress
            self.nicegui_log = nicegui_log
            self.command("step", step)
            self.close_callback = close_callback

        def command(self, command: str, value: Optional[float] = None):
            self.linear_progress.min = 0
            if command == "step":
                self.linear_progress.value = value
            elif command == "close":
                self.linear_progress.value = 1.0
                if self.close_callback is not None:
                    self.close_callback()
            else:
                raise ValueError(f"Unknown command: {command}")

        def emit(self, record):
            try:
                # get message
                msg = self.format(record)

                # push message to log
                self.nicegui_log.push(msg)
            except RecursionError:  # See issue 36272
                raise
            except Exception:
                self.handleError(record)

    def __init__(self, action_key: str, level=logging.NOTSET):
        super().__init__(action_key, level)
        self._step = 0
        self._steps = 1

        # add logger to root logger
        logging.root.manager.loggerDict[action_key] = self

    def __del__(self):
        if len(self.handlers) > 0 and self.is_logger_exist(self.name):
            self.close()

    def _command(self, command: str, value: Optional[float] = None):
        for handler in [handler for handler in self.handlers if isinstance(handler, ActionLogger.ActionLoggerHandler)]:
            handler.command(command, value)

    @classmethod
    def is_logger_exist(cls, action_key: str) -> bool:
        # get all logger
        all_loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]

        # check if logger already exists
        for _logger in all_loggers:
            if _logger.name != action_key:
                continue
            if not isinstance(_logger, ActionLogger):
                continue
            return True
        return False

    def is_logger_ready(self) -> bool:
        return len(self.handlers) > 0 and self.is_logger_exist(self.name)

    async def wait_for_logger(self, timeout: int = 60):
        wait_start = asyncio.get_event_loop().time()
        while not self.is_logger_ready():
            if asyncio.get_event_loop().time() - wait_start > timeout:
                raise RuntimeError("Timeout while waiting for logger to be ready.")
            await asyncio.sleep(0.001)

    async def configure_logger(self, nicegui_linear_progress: ui.linear_progress, nicegui_log: ui.log, close_callback: Optional[callable] = None):
        # check if logger already configured
        if self.is_logger_ready():
            raise RuntimeError("Logger is already configured.")

        # create handler
        handler = self.ActionLoggerHandler(nicegui_linear_progress=nicegui_linear_progress,
                                           nicegui_log=nicegui_log,
                                           step=self.step,
                                           close_callback=close_callback)
        # add handler to logger
        self.addHandler(handler)

        # log initial message
        self.debug("<Logger initialized>")

    def close(self):
        # log final message
        self.debug("<Logger closed>")

        # send final command
        self._command("close")

        # remove all handlers
        for handler in self.handlers:
            self.removeHandler(handler)

        # remove logger from root logger
        if self.is_logger_exist(self.name):
            logging.root.manager.loggerDict.pop(self.name)

    def next_step(self):
        self.step += 1

    @property
    def step(self) -> int:
        return self._step

    @step.setter
    def step(self, value: int):
        self._step = value
        if self.is_logger_ready():
            self._command("step", self._step / self.steps)

    @property
    def steps(self) -> int:
        return self._steps

    @steps.setter
    def steps(self, value: int):
        self._steps = value
        if self.is_logger_ready():
            self._command("step", self._step / self.steps)

    def finalize(self):
        self.step = self.steps
        self.close()


class CustomActionAdmin(BaseAdmin):
    class ActionLoggerContextManager:
        def __init__(self, action_key: str):
            self.action_key = action_key

            # check if logger already exists
            if ActionLogger.is_logger_exist(action_key):
                raise ActionFailed("Action already in progress.")

            # create logger
            self.logger = ActionLogger(action_key=action_key)

            # check if logger now exists
            if not ActionLogger.is_logger_exist(action_key):
                raise ActionFailed("Could not create action logger.")

        def __enter__(self):
            return self.logger

        def __exit__(self, exc_type, exc_val, exc_tb):
            # close logger
            self.logger.close()

    async def handle_action(self, request: Request) -> Response:
        request.state.action = RequestAction.ACTION
        try:
            identity = request.path_params.get("identity")
            pks = request.query_params.getlist("pks")
            name = not_none(request.query_params.get("name"))
            action_key = not_none(request.query_params.get("action-key"))
            model = self._find_model_from_identity(identity)
            if not model.is_accessible(request):
                raise ActionFailed("Forbidden")
            with self.ActionLoggerContextManager(action_key) as action_logger:
                # add action logger to request state
                request.state.action_logger = action_logger

                # handle action
                handler_return = await model.handle_action(request, pks, name)
            # remove action logger from request state
            del request.state.action_logger

            if isinstance(handler_return, Response):
                return handler_return
            return JSONResponse({"msg": handler_return})
        except ActionFailed as exc:
            return JSONResponse({"msg": exc.msg}, status_code=HTTP_400_BAD_REQUEST)

    async def handle_row_action(self, request: Request) -> Response:
        request.state.action = RequestAction.ROW_ACTION
        try:
            identity = request.path_params.get("identity")
            pk = request.query_params.get("pk")
            name = not_none(request.query_params.get("name"))
            model = self._find_model_from_identity(identity)
            if not model.is_accessible(request):
                raise ActionFailed("Forbidden")
            handler_return = await model.handle_row_action(request, pk, name)
            if isinstance(handler_return, Response):
                return handler_return
            return JSONResponse({"msg": handler_return})
        except ActionFailed as exc:
            return JSONResponse({"msg": exc.msg}, status_code=HTTP_400_BAD_REQUEST)


class MyAdmin(Admin, CustomActionAdmin):
    ...


# Create admin
admin = MyAdmin(title="Test Admin",
                statics_dir="statics")


class Test(Document):
    meta = {"collection": "test"}

    test_str = StringField()


class TestView(ModelView):
    def __init__(self):
        super().__init__(document=Test, icon="fa fa-server", name="Test", label="Test")

    actions = ["delete", "test_action"]

    def _additional_css_links(self, request: Request, action: RequestAction) -> Sequence[str]:
        links = super()._additional_css_links(request, action)
        if action == RequestAction.LIST:
            links.append("/admin/statics/css/modal.css")

        return links

    @action(name="test_action",
            text="Test Action")
    # confirmation="Möchtest du die Test Aktion durchführen?",
    # icon_class="fa-regular fa-network-wired",
    # submit_btn_text="Ja, fortsetzen",
    # submit_btn_class="btn-success")
    async def test_action(self, request: Request, pk: list[str]) -> str:
        # get logger
        action_logger: ActionLogger = request.state.action_logger
        action_logger.steps = 3

        # wait for logger to be ready
        await action_logger.wait_for_logger(5)

        # step 1
        action_logger.info("Step 1")
        await asyncio.sleep(1)
        action_logger.step = 1

        # step 2
        action_logger.info("Step 2")
        await asyncio.sleep(1)
        action_logger.step = 2

        # await asyncio.sleep(1)
        # action_logger.steps += 1000
        # for i in range(1000):
        #     action_logger.info(f"Step 1 - {i}")
        #     await asyncio.sleep(0.01)
        #     action_logger.step += 1

        # step 3
        action_logger.info("Step 3")
        await asyncio.sleep(1)
        action_logger.step = 3

        # final step
        action_logger.finalize()
        return "Test Aktion erfolgreich."


# Add views to admin#
admin.add_view(TestView())

# Mount admin to app
admin.mount_to(app)


@ui.page("/action_log/{action_key}")
def action_log(action_key: str = "null"):
    if action_key == "" or action_key == "null":
        ui.label("No action key provided.")
        return

    async def configur_logger():
        if not ActionLogger.is_logger_exist(action_key):
            return

        # get logger
        action_logger = logging.getLogger(action_key)
        if not isinstance(action_logger, ActionLogger):
            raise RuntimeError("Logger is not an ActionLogger.")
        await action_logger.configure_logger(progress, log)

        # disable timer
        timer.cancel()

    # create ui elements
    with ui.row().style("height: 10px; width: 100%; padding-left: 15px; padding-right: 15px;"):
        progress = ui.linear_progress(show_value=False).classes("w-full h-full").style("margin: 0px;")
    with ui.scroll_area().style("height: 558px; margin-top: -16px; margin-left: 0px; margin-right: 0px; margin-bottom: 0px;"):
        log = ui.log().classes("w-full h-full").style("margin-top: -16px; margin-left: 0px; margin-right: 0px; margin-bottom: -16px;")

    # run timer
    timer = ui.timer(1, lambda: configur_logger())


# Run nicegui
ui.run_with(app=app,
            mount_path="/nicegui")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
