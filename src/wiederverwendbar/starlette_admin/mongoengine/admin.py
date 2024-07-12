from jinja2 import PackageLoader
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette_admin.contrib.mongoengine import Admin as BaseAdmin


class Admin(BaseAdmin):
    def init_routes(self) -> None:
        super().init_routes()

        # find the statics mount index
        statics_index = None
        for i, route in enumerate(self.routes):
            if isinstance(route, Mount) and route.name == "statics":
                statics_index = i
                break
        if statics_index is None:
            raise ValueError("Could not find statics mount")

        # override the static files route
        self.routes[statics_index] = Mount("/statics",
                                           app=StaticFiles(
                                               directory=self.statics_dir,
                                               packages=[("wiederverwendbar", "starlette_admin/statics"), "starlette_admin"]),
                                           name="statics")

    def _setup_templates(self) -> None:
        super()._setup_templates()
        additional_loaders = [
            PackageLoader("wiederverwendbar", "starlette_admin/mongoengine/generic_embedded_document_field/templates"),
        ]

        self.templates.env.loader.loaders.extend(additional_loaders)
