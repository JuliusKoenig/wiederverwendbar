import logging
import asyncio

import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette.requests import Request
from starlette_admin.contrib.mongoengine import ModelView
from starlette_admin.actions import action
from mongoengine import connect, Document, StringField

from wiederverwendbar.starlette_admin import AuthAdminSettings, MongoengineAuthAdmin

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
        )
    ],
)


class MyAdmin(MongoengineAuthAdmin):
    ...


# Create admin
admin = MyAdmin(settings=AuthAdminSettings(admin_debug=True, admin_auth=True, admin_static_dir="statics", admin_superuser_auto_create=True))


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
        return "Test Aktion erfolgreich."


# Add views to admin#
admin.add_view(TestView())

# Mount admin to app
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
