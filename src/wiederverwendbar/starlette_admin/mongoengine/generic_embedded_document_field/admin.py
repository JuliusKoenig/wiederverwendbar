from jinja2 import PackageLoader
from starlette_admin.contrib.mongoengine import Admin as MongoengineAdmin

from wiederverwendbar.starlette_admin.multi_path.admin import MultiPathAdminMeta, MultiPathAdmin
from wiederverwendbar.starlette_admin.settings.admin import SettingsAdminMeta
from wiederverwendbar.starlette_admin.form_max_fields.admin import FormMaxFieldsAdmin
from wiederverwendbar.starlette_admin.action_log.admin import ActionLogAdminMeta

# class GenericEmbeddedAdminMeta(SettingsAdminMeta, MultiPathAdminMeta): #todo: fix this
#     ...


class GenericEmbeddedAdmin(MongoengineAdmin, FormMaxFieldsAdmin, MultiPathAdmin, metaclass=ActionLogAdminMeta):
    form_max_fields = 10000
    static_files_packages = [("wiederverwendbar", "starlette_admin/mongoengine/generic_embedded_document_field/statics")]
    template_packages = [PackageLoader("wiederverwendbar", "starlette_admin/mongoengine/generic_embedded_document_field/templates")]
