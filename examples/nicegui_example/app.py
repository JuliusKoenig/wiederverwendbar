from typing import Union

from nicegui import ui


class UiApp:
    def __init__(self, core_app: Union["CoreApp"]) -> None:
        super().__init__()

        self.core_app = core_app

        # register exception handler
        # ui_app.on_exception(self.exception_handler) ToDo

        # add root route
        ui.page("/")(self.root)

        # initialize nicegui
        ui.run_with(
            app=self.core_app,
            title=settings.branding_title,
            viewport=settings.ui_viewport,
            # favicon=settings.ui_favicon, # ToDo favicon support
            dark=settings.ui_dark,
            language=settings.ui_language,
            reconnect_timeout=settings.ui_reconnect_timeout,
            mount_path=settings.ui_web_path,
            prod_js=settings.ui_prod_js,
            storage_secret=settings.ui_storage_secret,
        )

    @classmethod
    async def root(cls):
        if settings.ui_default_path is None:
            ui.label(settings.branding_title)
            ui.label("Nothing to see here.")
        else:
            ui.navigate.to(settings.ui_default_path)

    # @classmethod ToDo
    # async def exception_handler(cls, exception: UiException | BaseException) -> None:
    #     if not isinstance(exception, UiException):
    #         return
    #     await exception()
