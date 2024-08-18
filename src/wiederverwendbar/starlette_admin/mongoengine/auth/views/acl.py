from typing import Type, Optional, Sequence

from starlette.requests import Request
from starlette_admin import RequestAction

from starlette_admin.contrib.mongoengine.converters import BaseMongoEngineModelConverter

from wiederverwendbar.starlette_admin.mongoengine.auth.documents.acl import AccessControlList
from wiederverwendbar.starlette_admin.mongoengine.auth.views.model import ModelView
from wiederverwendbar.starlette_admin.mongoengine.helper import get_document_field
from wiederverwendbar.starlette_admin.mongoengine.view import MongoengineModelView
from wiederverwendbar.starlette_admin.mongoengine.auth.fields import AccessControlListReferenceField


class AccessControlListView(ModelView, MongoengineModelView):
    exclude_fields_from_list = [AccessControlList.id,
                                AccessControlList.query_filter,
                                AccessControlList.allow_detail,
                                AccessControlList.allow_create,
                                AccessControlList.allow_update,
                                AccessControlList.specify_fields,
                                AccessControlList.allow_delete,
                                AccessControlList.allow_execute,
                                AccessControlList.specify_actions]
    exclude_fields_from_detail = [AccessControlList.id]
    exclude_fields_from_create = [AccessControlList.id]
    exclude_fields_from_edit = [AccessControlList.id]

    def __init__(
            self,
            document: Type[AccessControlList],
            reference_loader: callable,
            fields_loader: callable,
            actions_loader: callable,
            icon: Optional[str] = None,
            name: Optional[str] = None,
            label: Optional[str] = None,
            identity: Optional[str] = None,
            converter: Optional[BaseMongoEngineModelConverter] = None,
    ):
        # set default values
        document = document or AccessControlList
        icon = icon or "fa-solid fa-file-shield"
        label = label or "Zugriffskontrolllisten"

        fields = []
        for field_name in list(getattr(document, "_fields_ordered", [])):
            if field_name == "object":
                fields.append(AccessControlListReferenceField(name=field_name,
                                                              choices_loader=reference_loader,
                                                              required=get_document_field(document=document, field_name=field_name).required))
            elif field_name == "specify_fields":
                fields.append(AccessControlListReferenceField(name=field_name,
                                                              choices_loader=fields_loader,
                                                              required=get_document_field(document=document, field_name=field_name).required,
                                                              multiple=True))
            elif field_name == "specify_actions":
                fields.append(AccessControlListReferenceField(name=field_name,
                                                              choices_loader=actions_loader,
                                                              required=get_document_field(document=document, field_name=field_name).required,
                                                              multiple=True))
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
            elif field.name == "groups":
                field.label = "Gruppen"
            elif field.name == "object":
                field.label = "Objekt"
            elif field.name == "query_filter":
                field.label = "Filter"
            elif field.name == "allow_detail":
                field.label = "Erlaube Detailansicht"
            elif field.name == "allow_create":
                field.label = "Erlaube Erstellen"
            elif field.name == "allow_update":
                field.label = "Erlaube Aktualisieren"
            elif field.name == "specify_fields":
                field.label = "Spezifische Felder"
            elif field.name == "allow_delete":
                field.label = "Erlaube Löschen"
            elif field.name == "allow_execute":
                field.label = "Erlaube Ausführen"
            elif field.name == "specify_actions":
                field.label = "Spezifische Aktionen"

    def _additional_js_links(
            self, request: Request, action: RequestAction
    ) -> Sequence[str]:
        links = list(super()._additional_js_links(request, action))
        if action == RequestAction.CREATE or action == RequestAction.EDIT:
            links.append(request.url_for("admin:statics", path="js/acl_view.js"))
        return links
