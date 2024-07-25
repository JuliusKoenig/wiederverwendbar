from enum import Enum

import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from mongoengine import connect, Document, EmbeddedDocument, StringField, IntField, FloatField, BooleanField, ListField, DictField, EmbeddedDocumentField, \
    GenericEmbeddedDocumentField

from wiederverwendbar.starlette_admin import GenericEmbeddedAdmin, GenericEmbeddedConverter, GenericEmbeddedDocumentView

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
admin = GenericEmbeddedAdmin(title="Test Admin")


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

    test_emb = EmbeddedDocumentField(Test2)
    test_gen_emb = GenericEmbeddedDocumentField(choices=[Test1, Test2], help_text="Test Generic Embedded Document Field.")
    test_gen_emb_list = ListField(GenericEmbeddedDocumentField(choices=[Test1, Test2], help_text="Test Generic Embedded Document Field."))


class TestView(GenericEmbeddedDocumentView):
    def __init__(self):
        super().__init__(document=Test, icon="fa fa-server", name="Test", label="Test", converter=GenericEmbeddedConverter())


# Add views to admin#
admin.add_view(TestView())

# Mount admin to app
admin.mount_to(app)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
