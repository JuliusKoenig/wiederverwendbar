from jinja2 import PackageLoader

from wiederverwendbar.starlette_admin import MultiPathAdmin


class TestAdmin1(MultiPathAdmin):
    static_files_packages = [("wiederverwendbar", "starlette_admin/statics")]
    template_packages = [PackageLoader("wiederverwendbar", "starlette_admin/mongoengine/generic_embedded_document_field")]


class TestAdmin2(TestAdmin1):
    static_files_packages = [("wiederverwendbar", "starlette_admin/statics/js")]
    template_packages = [PackageLoader("wiederverwendbar", "starlette_admin/mongoengine/generic_embedded_document_field/templates")]


base_admin = MultiPathAdmin(title="Test Admin")
admin1 = TestAdmin1(title="Test Admin")
admin2 = TestAdmin2(title="Test Admin")
