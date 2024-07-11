from dataclasses import dataclass
from dataclasses import field as dc_field
from typing import Any, Dict, Type, Sequence, List

from starlette.requests import Request
from starlette.datastructures import FormData
from starlette_admin import RequestAction
from starlette_admin.helpers import extract_fields

import mongoengine as me
import starlette_admin as sa


@dataclass
class GenericEmbeddedDocumentField(sa.BaseField):
    embedded_doc_name_mapping: Dict[str, Type[me.EmbeddedDocument]] = dc_field(default_factory=dict)
    embedded_doc_fields: Dict[str, Sequence[sa.BaseField]] = dc_field(default_factory=dict)
    current_doc_name: str = ""
    render_function_key: str = "json"
    form_template: str = "forms/generic_embedded.html"
    display_template: str = "displays/generic_embedded.html"
    select2: bool = True

    def __post_init__(self) -> None:
        self.current_doc_name = ""
        super().__post_init__()
        self._propagate_id()

    def get_fields_list(
            self,
            request: Request,
            doc_name: str,
            action: RequestAction = RequestAction.LIST,
    ) -> Sequence[sa.BaseField]:
        _fields = []
        for current_doc_name, fields in self.embedded_doc_fields.items():
            if doc_name != "" and doc_name != current_doc_name:
                continue
            _fields.extend(extract_fields(fields, action))
        return _fields

    def _propagate_id(self) -> None:
        """Will update fields id by adding his id as prefix (ex: category.name)"""
        for doc_name, doc_fields in self.embedded_doc_fields.items():
            for field in doc_fields:
                field.id = self.id + ("_" if self.id else "") + doc_name + "_" + field.name
                if isinstance(field, type(self)):
                    field._propagate_id()

    async def parse_form_data(
            self, request: Request, form_data: FormData, action: RequestAction
    ) -> Any:
        # get selection field value
        doc_name = form_data.get(self.id, "")
        if doc_name == "":
            return None
        doc_type = self.embedded_doc_name_mapping.get(doc_name, None)
        if doc_type is None:
            raise ValueError(f"Invalid choice value: {doc_name}")

        # get selected embedded document fields
        doc_data = {}
        for field in self.get_fields_list(request, doc_name, action):
            doc_data[field.name] = await field.parse_form_data(request, form_data, action)

        # create embedded document
        doc_obj = doc_type(**doc_data)

        return doc_obj

    async def serialize_value(
            self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        # get embedded document name
        doc_name = None
        for name, doc_type in self.embedded_doc_name_mapping.items():
            if isinstance(value, doc_type):
                doc_name = name
                break
        if doc_name is None:
            raise ValueError(f"Invalid embedded document value: {value}")

        serialized_value: Dict[str, Any] = {}
        for field in self.get_fields_list(request, doc_name, action):
            name = field.name
            serialized_value[name] = None
            if hasattr(value, name) or (isinstance(value, dict) and name in value):
                field_value = (
                    getattr(value, name) if hasattr(value, name) else value[name]
                )
                if field_value is not None:
                    serialized_value[name] = await field.serialize_value(
                        request, field_value, action
                    )

        # add doc name to serialized value at detail and edit view
        if "__doc_name__" in serialized_value:
            raise ValueError(f"Field name '__doc_name__' is reserved")
        if action == RequestAction.EDIT or action == RequestAction.DETAIL:
            serialized_value["__doc_name__"] = doc_name
        return serialized_value

    def additional_css_links(
            self, request: Request, action: RequestAction
    ) -> List[str]:
        _links = []
        if self.select2 and action.is_form():
            _links.append(
                str(
                    request.url_for(
                        f"{request.app.state.ROUTE_NAME}:statics",
                        path="css/select2.min.css",
                    )
                )
            )
        for f in self.get_fields_list(request, "", action):
            _links.extend(f.additional_css_links(request, action))
        return _links

    def additional_js_links(self, request: Request, action: RequestAction) -> List[str]:
        _links = []
        if self.select2 and action.is_form():
            _links.append(
                str(
                    request.url_for(
                        f"{request.app.state.ROUTE_NAME}:statics",
                        path="js/vendor/select2.min.js",
                    )
                )
            )
        for f in self.get_fields_list(request, "", action):
            _links.extend(f.additional_js_links(request, action))
        return _links
