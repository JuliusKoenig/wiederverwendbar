from typing import Type, Any, Optional, Union
from starlette_admin.fields import BaseField
from starlette_admin.contrib.mongoengine import ModelView as MongoModelView


class PropertyModelView:
    property_field_position_before: Optional[dict[str, Union[str, Any]]] = None

    def __new__(cls, *args, **kwargs):
        # override __init__ method
        __original_init__ = getattr(cls, "__init__", None)

        def __init__(self, *a, **kw):
            # convert property_field_position_before to dict[str, str]
            if self.property_field_position_before is not None:
                property_field_position_before = {}
                for attr_name, attr in self.property_field_position_before.items():
                    if isinstance(attr, str):
                        property_field_position_before[attr_name] = attr
                    else:
                        if hasattr(attr, "name"):
                            property_field_position_before[attr_name] = attr.name
                        else:
                            raise ValueError(f"{attr} must have a name attribute.")
            else:
                property_field_position_before = None
            self.property_field_position_before = property_field_position_before

            # call original __init__ method
            if __original_init__ is not None:
                __original_init__(self, *a, **kw)

            # call __post_init__ method
            if hasattr(self, "__post_init__"):
                self.__post_init__()

        cls.__init__ = __init__

        return super().__new__(cls)

    def __post_init__(self):
        if isinstance(self, MongoModelView):
            for attr_name, attr in self.document.__dict__.items():
                if not isinstance(attr, property):
                    continue
                sa_field_type: Type[BaseField] = getattr(attr.fget, "__sa_field_type__", None)
                if sa_field_type is None:
                    continue
                sa_field_kwargs: dict[str, Any] = getattr(attr.fget, "__sa_field_kwargs__")

                allow_set = True if attr.fset is not None else False

                sa_field: BaseField = sa_field_type(**sa_field_kwargs)
                if not allow_set:
                    sa_field.exclude_from_create = True
                    sa_field.exclude_from_edit = True

                # position before another field
                property_field_position_before: dict[str, str] = getattr(self, "property_field_position_before", None)
                fields: list[BaseField] = getattr(self, "fields", [])
                searchable_fields: list[str] = getattr(self, "searchable_fields", [])
                sortable_fields: list[str] = getattr(self, "sortable_fields", [])
                exclude_fields_from_create: list[str] = getattr(self, "exclude_fields_from_create", [])
                exclude_fields_from_edit: list[str] = getattr(self, "exclude_fields_from_edit", [])
                if sa_field.name in property_field_position_before:
                    position_before = property_field_position_before[sa_field.name]
                    for i, field in enumerate(fields):
                        if field.name == position_before:
                            fields.insert(i, sa_field)
                            searchable_fields.insert(i, sa_field.name)
                            sortable_fields.insert(i, sa_field.name)
                            exclude_fields_from_create.insert(i, sa_field.name)
                            exclude_fields_from_edit.insert(i, sa_field.name)
                            break
                    else:
                        raise ValueError(f"Field {position_before} not found.")
                else:
                    fields.append(sa_field)
                    searchable_fields.append(sa_field.name)
                    sortable_fields.append(sa_field.name)
                    exclude_fields_from_create.append(sa_field.name)
                    exclude_fields_from_edit.append(sa_field.name)

                self.fields = fields
                self.searchable_fields = searchable_fields
                self.sortable_fields = sortable_fields
                if not allow_set:
                    self.exclude_fields_from_create = exclude_fields_from_create
                    self.exclude_fields_from_edit = exclude_fields_from_edit
        else:
            raise NotImplementedError(f"{self.__class__.__name__} is not supported yet.")
