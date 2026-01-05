from typing import Union

from jinja2 import BaseLoader, ChoiceLoader, FileSystemLoader, PackageLoader
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

from wiederverwendbar.starlette_admin.admin import BaseAdmin


class MultiPathAdminMeta(type):
    def __new__(cls, name, bases, attrs):
        # combine static_files_packages from bases and attrs
        all_static_files_packages = []
        # get all static_files_packages from bases
        for base in bases:
            if hasattr(base, "static_files_packages"):
                for static_files_package in base.static_files_packages:
                    # skip duplicates
                    if static_files_package in all_static_files_packages:
                        continue
                    # add at the beginning of the combined list
                    all_static_files_packages.append(static_files_package)
        # get static_files_packages from attrs
        if "static_files_packages" in attrs:
            for static_files_package in attrs["static_files_packages"]:
                # skip duplicates
                if static_files_package in all_static_files_packages:
                    continue
                # add at the beginning of the combined list
                all_static_files_packages.append(static_files_package)

        # set static_files_packages to the combined list
        attrs["static_files_packages"] = all_static_files_packages

        # combine template_packages from bases and attrs
        all_template_packages = []
        # get all template_packages from bases
        for base in bases:
            if hasattr(base, "template_packages"):
                for template_package in base.template_packages:
                    # skip duplicates
                    if template_package in all_template_packages:
                        continue
                    # add at the beginning of the combined list
                    all_template_packages.append(template_package)

        # get template_packages from attrs
        if "template_packages" in attrs:
            for template_package in attrs["template_packages"]:
                # skip duplicates
                if template_package in all_template_packages:
                    continue
                # add at the beginning of the combined list
                all_template_packages.append(template_package)

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

        # reverse static files packages
        self.static_files_packages.reverse()

        # override the static files route
        self.routes[statics_index] = Mount("/statics", app=StaticFiles(directory=self.statics_dir, packages=self.static_files_packages), name="statics")

    def _setup_templates(self) -> None:
        super()._setup_templates()

        # reverse template packages
        self.template_packages.reverse()

        self.templates.env.loader = ChoiceLoader(
            [
                FileSystemLoader(self.templates_dir),
                *self.template_packages,
            ]
        )
