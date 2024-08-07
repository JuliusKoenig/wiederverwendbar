from jinja2 import PackageLoader

from wiederverwendbar.starlette_admin.admin import MultiPathAdmin


class DropDownIconViewAdmin(MultiPathAdmin):
    template_packages = [PackageLoader("wiederverwendbar", "starlette_admin/drop_down_icon_view/templates")]
