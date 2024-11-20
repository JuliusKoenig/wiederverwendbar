from wiederverwendbar.starlette_admin import FormMaxFieldsAdmin, ActionLogAdmin, GenericEmbeddedAdmin
# from wiederverwendbar.starlette_admin.action_log.admin import ActionLogAdminMeta
# from wiederverwendbar.starlette_admin.mongoengine.generic_embedded_document_field.admin import GenericEmbeddedAdminMeta
#
# class AdminMeta(ActionLogAdminMeta, GenericEmbeddedAdminMeta):
#     ...


class Admin(ActionLogAdmin, GenericEmbeddedAdmin, FormMaxFieldsAdmin):#, metaclass=AdminMeta):
    ...


if __name__ == "__main__":
    ...
