import asyncio

import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette.requests import Request
from starlette_admin.contrib.mongoengine import ModelView
from starlette_admin.actions import action
from starlette_admin.views import CustomView, Link
from mongoengine import connect, Document, StringField

from wiederverwendbar.starlette_admin import AuthAdminSettings, MongoengineAuthAdmin, User

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

# Create admin
admin = MongoengineAuthAdmin(settings=AuthAdminSettings(admin_debug=True, admin_auth=True, admin_static_dir="statics", admin_superuser_auto_create=True))


class Test(Document):
    meta = {"collection": "test"}

    test_str = StringField()


class TestModelView(ModelView):
    def __init__(self):
        super().__init__(document=Test, icon="fa fa-server", name="TestModel", label="TestModel")

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


class TestCustomView(CustomView):
    def __init__(self):
        super().__init__(
            label="TestCustom",
            icon="fa-solid fa-wrench",
            path="/",
            template_path="index.html",
            name="TestCustom",
            methods=None,
            add_to_menu=True,
        )


class TestLinkView(Link):
    def __init__(self):
        super().__init__(
            label="TestLink",
            icon="fa-solid fa-wrench",
            url="/",
            target="_blank",
        )


# Add views to admin#
admin.add_view(TestModelView())
admin.add_view(TestCustomView())
admin.add_view(TestLinkView())

# Mount admin to app
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
