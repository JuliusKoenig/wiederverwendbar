from dataclasses import dataclass
from dataclasses import field as dc_field
from typing import Any, Dict, Type, Sequence, List, Optional

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
    render_function_key: str = "json"
    form_template: str = "forms/generic_embedded.html"
    display_template: str = "displays/generic_embedded.html"
    select2: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        self._propagate_id()

    @property
    def fieldset_id(self) -> str:
        if self.id == "":
            return "fieldset"
        return self.id + ".fieldset"

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
                field.id = self.id + ("." if self.id else "") + doc_name + "." + field.name
                if isinstance(field, type(self)):
                    field._propagate_id()

    def _add_doc_data(self, doc_data: Dict[str, Any], doc_name: str, doc_type: Type[me.EmbeddedDocument]) -> Dict[str, Any]:
        # add doc name to serialized value at detail and edit view
        if "__doc_name__" in doc_data:
            raise ValueError(f"Field name '__doc_name__' is reserved")
        doc_data["__doc_name__"] = doc_name

        return doc_data

    async def convert_generic_embedded_document(self, request: Request, value: Dict[str, Any]) -> Any:
        doc_name = value.pop("__doc_name__", "")
        if doc_name == "":
            raise ValueError(f"Field name '__doc_name__' not found in value: {value}")
        doc_type = self.embedded_doc_name_mapping.get(doc_name, None)
        if doc_type is None:
            raise ValueError(f"Invalid choice value: {doc_name}")

        embedded_doc = doc_type(**value)
        return embedded_doc

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

        # add doc name to serialized value at detail and edit view
        if "__doc_name__" in doc_data:
            raise ValueError(f"Field name '__doc_name__' is reserved")
        if action in (RequestAction.DETAIL, RequestAction.CREATE, RequestAction.EDIT):
            doc_data["__doc_name__"] = doc_name

        return doc_data

    async def serialize_value(
            self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        # get embedded document name
        doc_name = None
        doc_type = None
        for name, doc_type in self.embedded_doc_name_mapping.items():
            if isinstance(value, doc_type):
                doc_name = name
                doc_type = doc_type
                break
        if doc_name is None or doc_type is None:
            raise ValueError(f"Invalid embedded document value: {value}")

        # return doc name at list view if render function is text
        if action == RequestAction.LIST and self.render_function_key == "text":
            return doc_name

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
        if action in (RequestAction.DETAIL, RequestAction.CREATE, RequestAction.EDIT):
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
            _links.append(
                str(
                    request.url_for(
                        f"{request.app.state.ROUTE_NAME}:statics",
                        path="js/generic_embedded.js",
                    )
                )
            )
        for f in self.get_fields_list(request, "", action):
            _links.extend(f.additional_js_links(request, action))
        return _links


@dataclass(init=False)
class ListField(sa.ListField):
    def __post_init__(self) -> None:
        super().__post_init__()
        if isinstance(self.field, GenericEmbeddedDocumentField):
            self.field._propagate_id()

    async def parse_form_data(
            self, request: Request, form_data: FormData, action: RequestAction
    ) -> Any:
        indices = self._extra_indices(form_data)
        value = []
        for index in indices:
            self.field.id = f"{self.id}.{index}"
            if isinstance(self.field, sa.CollectionField):
                self.field._propagate_id()
            if isinstance(self.field, GenericEmbeddedDocumentField):
                self.field._propagate_id()
            value.append(await self.field.parse_form_data(request, form_data, action))
        return value

    def _field_at(self, idx: Optional[int] = None) -> sa.BaseField:
        super()._field_at(idx)
        if isinstance(self.field, GenericEmbeddedDocumentField):
            self.field._propagate_id()
        return self.field
