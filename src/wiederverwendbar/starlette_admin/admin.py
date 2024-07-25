from typing import Union

from jinja2 import BaseLoader, ChoiceLoader, FileSystemLoader, PackageLoader
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette_admin.base import BaseAdmin


class MultiPathAdminMeta(type):
    def __new__(cls, name, bases, attrs):
        # combine static_files_packages from bases and attrs
        all_static_files_packages = []
        # get all static_files_packages from bases
        for base in bases:
            if hasattr(base, "static_files_packages"):
                all_static_files_packages.extend(base.static_files_packages)
        # get static_files_packages from attrs
        if "static_files_packages" in attrs:
            for static_files_package in attrs["static_files_packages"]:
                # skip duplicates
                if static_files_package in all_static_files_packages:
                    continue
                # add at the beginning of the combined list
                all_static_files_packages.insert(0, static_files_package)

        # set static_files_packages to the combined list
        attrs["static_files_packages"] = all_static_files_packages

        # combine template_packages from bases and attrs
        all_template_packages = []
        # get all template_packages from bases
        for base in bases:
            if hasattr(base, "template_packages"):
                all_template_packages.extend(base.template_packages)

        # get template_packages from attrs
        if "template_packages" in attrs:
            for template_package in attrs["template_packages"]:
                # skip duplicates
                if template_package in all_template_packages:
                    continue
                # add at the beginning of the combined list
                all_template_packages.insert(0, template_package)

        # set template_packages to the combined list
        attrs["template_packages"] = all_template_packages

        return super().__new__(cls, name, bases, attrs)


class MultiPathAdmin(BaseAdmin, metaclass=MultiPathAdminMeta):
    """
    A base class for Admin classes that can be used in multiple paths.
    In detail, it combines the static_files_packages and template_packages from all bases and attrs.
    """

    static_files_packages: list[Union[str, tuple[str, str]]] = ["starlette_admin"]
    template_packages: list[BaseLoader] = [PackageLoader("starlette_admin", "templates")]

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
        self.routes[statics_index] = Mount("/statics", app=StaticFiles(directory=self.statics_dir, packages=self.static_files_packages), name="statics")

    def _setup_templates(self) -> None:
        super()._setup_templates()

        self.templates.env.loader = ChoiceLoader(
            [
                FileSystemLoader(self.templates_dir),
                *self.template_packages,
            ]
        )


class FormMaxFieldsAdmin(BaseAdmin):
    form_max_fields: int = 1000

    async def _render_create(self, request: Request) -> Response:
        self._form_func = request.form
        request.form = self.form

        return await super()._render_create(request)

    async def _render_edit(self, request: Request) -> Response:
        self._form_func = request.form
        request.form = self.form

        return await super()._render_edit(request)

    async def form(self, *args, **kwargs):
        if "max_fields" not in kwargs:
            kwargs["max_fields"] = self.form_max_fields

        return await self._form_func(*args, **kwargs)
