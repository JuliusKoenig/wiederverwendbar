from jinja2 import PackageLoader
from starlette_admin.contrib.mongoengine import Admin as MongoengineAdmin

from wiederverwendbar.starlette_admin.admin import MultiPathAdmin, FormMaxFieldsAdmin


class GenericEmbeddedAdmin(MongoengineAdmin, FormMaxFieldsAdmin, MultiPathAdmin):
    form_max_fields = 10000
    static_files_packages = [("wiederverwendbar", "starlette_admin/mongoengine/generic_embedded_document_field/statics")]
    template_packages = [PackageLoader("wiederverwendbar", "starlette_admin/mongoengine/generic_embedded_document_field/templates")]
