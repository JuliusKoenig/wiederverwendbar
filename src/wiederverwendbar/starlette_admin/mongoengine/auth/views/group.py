from typing import Type, Optional, Callable, Union, Sequence, Tuple, Any

from starlette.requests import Request
from starlette_admin.contrib.mongoengine.converters import BaseMongoEngineModelConverter
from starlette_admin.fields import EnumField

from wiederverwendbar.starlette_admin.mongoengine.auth.documents.group import Group
from wiederverwendbar.starlette_admin.mongoengine.auth.views.model import ModelView
from wiederverwendbar.starlette_admin.mongoengine.helper import get_document_field
from wiederverwendbar.starlette_admin.mongoengine.view import MongoengineModelView


class GroupView(ModelView, MongoengineModelView):
    exclude_fields_from_list = [Group.id,
                                Group.company_logo,
                                Group.acls]
    exclude_fields_from_detail = [Group.id]
    exclude_fields_from_create = [Group.id]
    exclude_fields_from_edit = [Group.id]

    def __init__(
            self,
            document: Type[Group],
            icon: Optional[str] = None,
            name: Optional[str] = None,
            label: Optional[str] = None,
            identity: Optional[str] = None,
            converter: Optional[BaseMongoEngineModelConverter] = None,
            company_logo_choices_loader: Optional[Callable[[Request], Union[Sequence[str], Sequence[Tuple[Any, str]]]]] = lambda _: [],
    ):
        # set default values
        document = document or Group
        icon = icon or "fa fa-users"
        label = label or "Gruppe"

        fields = []
        for field_name in list(getattr(document, "_fields_ordered", [])):
            if field_name == "company_logo":
                fields.append(
                    EnumField(name=field_name, choices_loader=company_logo_choices_loader, required=get_document_field(document=document, field_name=field_name).required))
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
            if field.name == "name":
                field.label = "Gruppenname"
            elif field.name == "company_logo":
                field.label = "Firmenlogo"
            elif field.name == "users":
                field.label = "Benutzer"
            elif field.name == "acls":
                field.label = "Zugriffskontrolllisten"
