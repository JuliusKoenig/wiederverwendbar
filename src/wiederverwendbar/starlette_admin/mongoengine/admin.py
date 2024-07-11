from jinja2 import PackageLoader
from starlette_admin.contrib.mongoengine import Admin as BaseAdmin


class Admin(BaseAdmin):
    def _setup_templates(self) -> None:
        super()._setup_templates()
        additional_loaders = [
            PackageLoader("wiederverwendbar", "starlette_admin/mongoengine/generic_embedded_document_field/templates"),
        ]

        self.templates.env.loader.loaders.extend(additional_loaders)
