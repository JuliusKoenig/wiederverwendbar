from typing import Type, Optional

from starlette_admin.contrib.mongoengine.converters import BaseMongoEngineModelConverter

from wiederverwendbar.starlette_admin.mongoengine.auth.documents.acl import AccessControlList
from wiederverwendbar.starlette_admin.mongoengine.view import MongoengineModelView
from wiederverwendbar.starlette_admin.mongoengine.auth.fields import AccessControlListReferenceField


class AccessControlListView(MongoengineModelView):
    exclude_fields_from_list = [AccessControlList.id,
                                AccessControlList.users,
                                AccessControlList.allow_read,
                                AccessControlList.read_specify,
                                AccessControlList.allow_create,
                                AccessControlList.create_specify,
                                AccessControlList.allow_update,
                                AccessControlList.edit_specify,
                                AccessControlList.allow_delete,
                                AccessControlList.delete_specify]
    exclude_fields_from_detail = [AccessControlList.id]
    exclude_fields_from_create = [AccessControlList.id]
    exclude_fields_from_edit = [AccessControlList.id]

    def __init__(
            self,
            document: Type[AccessControlList],
            read_specify_loader: callable,
            create_specify_loader: callable,
            edit_specify_loader: callable,
            delete_specify_loader: callable,
            icon: Optional[str] = None,
            name: Optional[str] = None,
            label: Optional[str] = None,
            identity: Optional[str] = None,
            converter: Optional[BaseMongoEngineModelConverter] = None,
    ):
        # set default values
        document = document or AccessControlList
        icon = icon or "fa-solid fa-file-shield"
        name = name or "ACL"
        label = label or "ACL"

        fields = []
        for field_name in list(getattr(document, "_fields_ordered", [])):
            if field_name == "read_specify":
                fields.append(AccessControlListReferenceField(name=field_name, choices_loader=read_specify_loader, multiple=True))
            elif field_name == "create_specify":
                fields.append(AccessControlListReferenceField(name=field_name, choices_loader=create_specify_loader, multiple=True))
            elif field_name == "edit_specify":
                fields.append(AccessControlListReferenceField(name=field_name, choices_loader=edit_specify_loader, multiple=True))
            elif field_name == "delete_specify":
                fields.append(AccessControlListReferenceField(name=field_name, choices_loader=delete_specify_loader, multiple=True))
            else:
                fields.append(field_name)
        self.fields = fields

        super().__init__(document=document,
                         icon=icon,
                         name=name,
                         label=label,
                         identity=identity,
                         converter=converter)
        for field in self.fields:
            if field.name == "users":
                field.label = "Benutzer"
            elif field.name == "allow_read":
                field.label = "Erlaube Lesen"
            elif field.name == "allow_create":
                field.label = "Erlaube Erstellen"
            elif field.name == "allow_update":
                field.label = "Erlaube Aktualisieren"
            elif field.name == "allow_delete":
                field.label = "Erlaube Löschen"
            elif field.name == "read_specify" or field.name == "create_specify" or field.name == "edit_specify" or field.name == "delete_specify":
                field.label = "Spezifiziere"