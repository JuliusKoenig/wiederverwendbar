from nicegui import ui

from wiederverwendbar.nicegui import NiceGUIApp

from tests.nicegui_test.settings import settings


class MyUi(NiceGUIApp):
    ...


ui_app = MyUi(settings=settings.ui,
              branding_settings=settings.branding)


@ui.page("/home")
def main_page():
    ui.label("test ui label")
