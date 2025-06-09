import logging
import asyncio

import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette.requests import Request
from starlette_admin.contrib.mongoengine import Admin, ModelView
from starlette_admin.actions import action
from mongoengine import Document, StringField
from kombu import Connection

from wiederverwendbar.functions.test_file import test_file
from wiederverwendbar.mongoengine import MongoengineDbSingleton
from wiederverwendbar.starlette_admin import ActionLogAdmin, ActionLogger, FormCommand, MultiPathAdmin, DownloadCommand

logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)

# connect to database
MongoengineDbSingleton(init=True)

# create kombu connection
kombu_connection = Connection(MongoengineDbSingleton().connection_string)


# Create starlette app
app = Starlette(
    routes=[
        Route(
            "/",
            lambda r: HTMLResponse("<a href=/admin/>Click me to get to Admin!</a>"),
        ),
    ],
)


class MyAdmin(Admin, ActionLogAdmin, MultiPathAdmin):
    ...


# Create admin
admin = MyAdmin(title="Test Admin", kombu_connection=kombu_connection)


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
        with await ActionLogger(request, parent=logger) as action_logger:
            # use context manager to ensure that the logger is finalized
            with action_logger.sub_logger("sub_action_1", "Sub Action 1", steps=3, ignore_loggers_like=["pymongo"]) as sub_logger:
                sub_logger_yes_no = sub_logger.yes_no("Möchtest du eine Testdatei generieren?")()
                if not sub_logger_yes_no:
                    sub_logger.finalize(success=False, on_error_msg="Test Aktion abgebrochen.")
                generated_file = test_file(1, 'MB')
                DownloadCommand(sub_logger, text="Testdatei", file_path=generated_file)()

        return "Test Aktion erfolgreich."


# Add views to admin#
admin.add_view(TestView())

# Mount admin to app
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
