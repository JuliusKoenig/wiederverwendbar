import logging
import asyncio
import threading
import time
from typing import Optional

import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette.requests import Request
from starlette_admin.contrib.mongoengine import Admin, ModelView
from starlette_admin.actions import action
from mongoengine import connect, Document, StringField

from wiederverwendbar.starlette_admin import ActionLogAdmin, ActionLogger

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
            lambda r: HTMLResponse("<a href=/admin/>Click me to get to Admin!</a>"),
        ),
    ],
)


class MyAdmin(Admin, ActionLogAdmin):
    ...


# Create admin
admin = MyAdmin(title="Test Admin")


class Test(Document):
    meta = {"collection": "test"}

    test_str = StringField()


class TestView(ModelView):
    def __init__(self):
        super().__init__(document=Test, icon="fa fa-server", name="Test", label="Test")

    actions = ["delete", "test_action_normal", "test_action_action_log"]

    @action(name="test_action_normal",
            text="Test Action - Normal")
    # confirmation="Möchtest du die Test Aktion durchführen?",
    # icon_class="fa-regular fa-network-wired",
    # submit_btn_text="Ja, fortsetzen",
    # submit_btn_class="btn-success")
    async def test_action_normal(self, request: Request, pk: list[str]) -> str:
        await asyncio.sleep(2)

        return "Test Aktion erfolgreich."

    @action(name="test_action_action_log",
            text="Test Action - Action Log")
    # confirmation="Möchtest du die Test Aktion durchführen?",
    # icon_class="fa-regular fa-network-wired",
    # submit_btn_text="Ja, fortsetzen",
    # submit_btn_class="btn-success")
    async def test_action_action_log(self, request: Request, pk: list[str]) -> str:
        with ActionLogger(request, parent=logger) as action_logger:
            action_thread = ActionThread(action_logger=action_logger, payload=payload, name="action_thrad_1", title="Action Thread 1")
            action_thread.start()
            await action_thread.wait(timeout=5)

        return "Test Aktion erfolgreich."


class ActionThread(threading.Thread):
    def __init__(self,
                 action_logger: ActionLogger,
                 name: str,
                 payload: Optional[callable] = None,
                 payload_args: Optional[list] = None,
                 payload_kwargs: Optional[dict] = None,
                 title: Optional[str] = None,
                 log_level: int = logging.NOTSET,
                 parent: Optional[logging.Logger] = None,
                 formatter: Optional[logging.Formatter] = None,
                 steps: Optional[int] = None,
                 on_success_msg: Optional[str] = None,
                 on_error_msg: Optional[str] = "Something went wrong.",
                 show_errors: Optional[bool] = None,
                 halt_on_error: Optional[bool] = None,
                 use_context_logger_level: bool = True,
                 use_context_logger_level_on_not_set: Optional[bool] = None,
                 ignore_loggers_equal: Optional[list[str]] = None,
                 ignore_loggers_like: Optional[list[str]] = None,
                 handle_origin_logger: bool = True,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

        self.lock = threading.Lock()
        self._payload = payload
        self._payload_args = payload_args if payload_args is not None else []
        self._payload_kwargs = payload_kwargs if payload_kwargs is not None else {}

        self._action_logger = action_logger
        self._sub_logger = None

        self._name = name
        self._title = title
        self._log_level = log_level
        self._parent = parent
        self._formatter = formatter
        self._steps = steps
        self._on_success_msg = on_success_msg
        self._on_error_msg = on_error_msg
        self._show_errors = show_errors
        self._halt_on_error = halt_on_error
        self._use_context_logger_level = use_context_logger_level
        self._use_context_logger_level_on_not_set = use_context_logger_level_on_not_set
        self._ignore_loggers_equal = ignore_loggers_equal
        self._ignore_loggers_like = ignore_loggers_like
        self._handle_origin_logger = handle_origin_logger

    def run(self):
        with self._action_logger.sub_logger(name=self._name,
                                            title=self._title,
                                            log_level=self._log_level,
                                            parent=self._parent,
                                            formatter=self._formatter,
                                            steps=self._steps,
                                            on_success_msg=self._on_success_msg,
                                            on_error_msg=self._on_error_msg,
                                            show_errors=self._show_errors,
                                            halt_on_error=self._halt_on_error,
                                            use_context_logger_level=self._use_context_logger_level,
                                            use_context_logger_level_on_not_set=self._use_context_logger_level_on_not_set,
                                            ignore_loggers_equal=self._ignore_loggers_equal,
                                            ignore_loggers_like=self._ignore_loggers_like,
                                            handle_origin_logger=self._handle_origin_logger) as sub_logger:
            self._sub_logger = sub_logger
            try:
                self.payload()
            except Exception as e:
                with self.lock:
                    self._sub_logger.finalize(success=False, on_error_msg=str(e))
            self._sub_logger.finalize(success=True)

    async def wait(self, timeout: int = -1):
        start_wait = time.perf_counter()
        while self.is_alive():
            if timeout != -1:
                if time.perf_counter() - start_wait > timeout:
                    with self.lock:
                        self._sub_logger.finalize(success=False, on_error_msg="Thread timed out.")
            await asyncio.sleep(0.1)

    def payload(self):
        if self._payload is None:
            raise NotImplementedError("Payload not implemented.")
        self._payload(*self._payload_args, **self._payload_kwargs)


def payload():
    while True:
        t_logger = logging.getLogger("test_foo")
        t_logger.debug("foo")
        print("foo")
        time.sleep(1)


# Add views to admin#
admin.add_view(TestView())

# Mount admin to app
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
