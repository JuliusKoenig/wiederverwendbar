from copy import deepcopy
from enum import Enum
from typing import Dict, Any

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route
from mongoengine import connect, Document, EmbeddedDocument, StringField, IntField, FloatField, BooleanField, ListField, DictField, EmbeddedDocumentField, \
    GenericEmbeddedDocumentField, ValidationError
from starlette_admin.contrib.mongoengine import ModelView

from wiederverwendbar.starlette_admin.mongoengine import Admin, GenericEmbeddedConverter

# ---
from wiederverwendbar.starlette_admin.mongoengine.generic_embedded_document_field.field import ListField as sa_ListField
from wiederverwendbar.starlette_admin.mongoengine.generic_embedded_document_field.field import GenericEmbeddedDocumentField as sa_GenericEmbeddedDocumentField

# connect to database
connect("test",
        host="localhost",
        port=27017)

# Create starlette app
app = Starlette(
    routes=[
        Route(
            "/",
            lambda r: HTMLResponse('<a href="/admin/">Click me to get to Admin!</a>'),
        ),
    ],
)

# Create admin
admin = Admin(title="Test Admin")


class Test1(EmbeddedDocument):
    meta = {"name": "test1_qwe"}

    test_1_str = StringField()
    test_1_int = IntField()
    test_1_float = FloatField()
    test_1_bool = BooleanField()


class Test2(EmbeddedDocument):
    test_2_str = StringField()
    test_2_int = IntField()
    test_2_float = FloatField()
    test_2_bool = BooleanField()
    test_2_list = ListField(StringField())
    test_2_dict = DictField()


class TestEnum(Enum):
    A = "a"
    B = "b"
    C = "c"


class Test(Document):
    meta = {"collection": "test"}

    # test_str = StringField()
    # test_int = IntField()
    # test_float = FloatField()
    # test_bool = BooleanField()
    # test_list = ListField(me.StringField())
    # test_dict = DictField()
    # test_enum = EnumField(TestEnum)
    test_gen_emb = GenericEmbeddedDocumentField(choices=[Test1, Test2], help_text="Test Generic Embedded Document Field.")
    #test_gen_emb_list = ListField(GenericEmbeddedDocumentField(choices=[Test1, Test2], help_text="Test Generic Embedded Document Field."))
    # test_emb = EmbeddedDocumentField(Test2)

    # def to_mongo(self, *args, **kwargs):
    #     config_types = []
    #     for config in self.test_gen_emb_list:
    #         config_type = type(config)
    #         if config_type in config_types:
    #             raise ValidationError(f"Config type '{config_type}' is already set.", field_name=None, errors={"test_gen_emb_list": "Config type is already set."})
    #         config_types.append(config_type)
    #     return super().to_mongo(*args, **kwargs)


class TestView(ModelView):
    def __init__(self):
        super().__init__(document=Test, icon="fa fa-server", name="Test", label="Test", converter=GenericEmbeddedConverter())

    async def convert_generic_embedded_document(self, request: Request, data: Dict[str, Any], obj: Any) -> None:
        data = deepcopy(data)
        for field in self.fields:
            if isinstance(field, sa_GenericEmbeddedDocumentField):
                value = data.get(field.name)
                if value is None:
                    continue
                value = await field.convert_generic_embedded_document(request, value)
                setattr(obj, field.name, value)
            elif isinstance(field, sa_ListField) and isinstance(field.field, sa_GenericEmbeddedDocumentField):
                for index, item in enumerate(data.get(field.name, [])):
                    value = await field.field.convert_generic_embedded_document(request, item)
                    data[field.name][index] = value
                setattr(obj, field.name, data[field.name])

    async def before_create(
            self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        await self.convert_generic_embedded_document(request, data, obj)

    async def before_edit(
            self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        await self.convert_generic_embedded_document(request, data, obj)


# Add views to admin#
admin.add_view(TestView())

# Mount admin to app
admin.mount_to(app)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
