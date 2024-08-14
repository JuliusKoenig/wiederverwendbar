import logging
import asyncio

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
            # use context manager to ensure that the logger is finalized
            with action_logger.sub_logger("sub_action_1", "Sub Action 1", steps=3) as sub_logger:
                sub_logger.info("Test Aktion startet ...")
                sub_logger.debug("Debug")
                sub_logger.info("Test Aktion step 1")
                await asyncio.sleep(2)
                sub_logger.next_step()
                sub_logger.info("Test Aktion step 2")
                _ = 1 / 0  # raise exception
                # raise ActionFailed("Test Aktion fehlgeschlagen.")
                await asyncio.sleep(2)
                sub_logger.next_step()
                sub_logger.steps += 100
                for i in range(1, 100):
                    sub_logger.info(f"Test Aktion step 2 - {i}")
                    sub_logger.next_step()
                    await asyncio.sleep(0.1)
                sub_logger.info("Test Aktion step 3")
                await asyncio.sleep(2)

            sub_action_2_logger = action_logger.new_sub_logger("sub_action_2", "Sub Action 2")
            sub_action_2_logger.steps = 3
            sub_action_3_logger = action_logger.new_sub_logger("sub_action_3", "Sub Action 3")
            sub_action_3_logger.steps = 3
            sub_action_2_logger.info("Test Aktion startet ...")
            sub_action_3_logger.info("Test Aktion startet ...")
            await asyncio.sleep(2)
            sub_action_2_logger.next_step()
            sub_action_3_logger.next_step()
            await asyncio.sleep(2)
            sub_action_2_logger.next_step()
            sub_action_3_logger.next_step()
            sub_action_2_logger.finalize(success=False, on_error_msg="Test Aktion fehlgeschlagen.")
            sub_action_3_logger.finalize(success=True, on_success_msg="Test Aktion erfolgreich.")

        return "Test Aktion erfolgreich."


# Add views to admin#
admin.add_view(TestView())

# Mount admin to app
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
