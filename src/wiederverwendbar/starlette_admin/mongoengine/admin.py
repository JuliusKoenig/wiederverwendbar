from jinja2 import PackageLoader
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette_admin.contrib.mongoengine import Admin as BaseAdmin


class Admin(BaseAdmin):
    def init_routes(self) -> None:
        super().init_routes()

        # override the static files route
        if not type(self.routes[0]) is Mount:
            raise ValueError("First route must be a Mount")
        statics = StaticFiles(directory=self.statics_dir, packages=[("wiederverwendbar", "starlette_admin/statics"), "starlette_admin"])
        mount = Mount("/statics", app=statics, name="statics")
        self.routes[0] = mount

    def _setup_templates(self) -> None:
        super()._setup_templates()
        additional_loaders = [
            PackageLoader("wiederverwendbar", "starlette_admin/mongoengine/generic_embedded_document_field/templates"),
        ]

        self.templates.env.loader.loaders.extend(additional_loaders)
