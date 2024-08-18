from typing import Type, Optional, Callable, Union, Sequence, Tuple, Any

from starlette.requests import Request
from starlette_admin.contrib.mongoengine.converters import BaseMongoEngineModelConverter
from starlette_admin.fields import PasswordField, EnumField

from wiederverwendbar.starlette_admin.mongoengine.auth.documents.user import User
from wiederverwendbar.starlette_admin.mongoengine.auth.views.model import ModelView
from wiederverwendbar.starlette_admin.mongoengine.helper import get_document_field
from wiederverwendbar.starlette_admin.mongoengine.view import MongoengineModelView


class UserView(ModelView, MongoengineModelView):
    exclude_fields_from_list = [User.id,
                                "password",
                                User.sessions,
                                User.company_logo,
                                User.acls]
    exclude_fields_from_detail = [User.id,
                                  "password"]
    exclude_fields_from_create = [User.id,
                                  User.password_change_time,
                                  User.sessions]
    exclude_fields_from_edit = [User.id,
                                User.password_change_time,
                                User.sessions]

    def __init__(
            self,
            document: Type[User],
            icon: Optional[str] = None,
            name: Optional[str] = None,
            label: Optional[str] = None,
            identity: Optional[str] = None,
            converter: Optional[BaseMongoEngineModelConverter] = None,
            company_logo_choices_loader: Optional[Callable[[Request], Union[Sequence[str], Sequence[Tuple[Any, str]]]]] = lambda _: [],
    ):
        # set default values
        document = document or User
        icon = icon or "fa fa-user"
        label = label or "Benutzer"

        fields = []
        for field_name in list(getattr(document, "_fields_ordered", [])):
            if field_name == "password_doc":
                fields.append(PasswordField(name="password", required=get_document_field(document=document, field_name=field_name).required))
            elif field_name == "company_logo":
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
                field.label = "Benutzername"
            elif field.name == "password":
                field.label = "Passwort"
            elif field.name == "password_change_time":
                field.label = "Passwortänderungszeit"
            elif field.name == "password_expiration_time":
                field.label = "Passwortablaufzeit"
            elif field.name == "avatar":
                field.label = "Profilbild"
            elif field.name == "company_logo":
                field.label = "Firmenlogo"
            elif field.name == "sessions":
                field.label = "Sitzungen"
            elif field.name == "admin":
                field.label = "Administrator"
            elif field.name == "groups":
                field.label = "Gruppen"
            elif field.name == "acls":
                field.label = "Zugriffskontrolllisten"
