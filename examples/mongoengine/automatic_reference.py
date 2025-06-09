from mongoengine import ListField, ReferenceField, StringField

from wiederverwendbar.mongoengine import AutomaticReferenceDocument


# --- example classes ---

class Test1(AutomaticReferenceDocument):
    meta = {"collection": "test1"}

    name = StringField(required=True)
    test2_one_to_one = ReferenceField("Test2", automatic_reference="test1_one_to_one")
    test2_one_to_many = ReferenceField("Test2", automatic_reference="test1_many_to_one")
    test2_many_to_one = ListField(ReferenceField("Test2"), automatic_reference="test1_one_to_many")
    test2_many_to_many = ListField(ReferenceField("Test2"), automatic_reference="test1_many_to_many")


class Test2(AutomaticReferenceDocument):
    meta = {"collection": "test2"}

    name = StringField(required=True)
    test1_one_to_one = ReferenceField("Test1", automatic_reference="test2_one_to_one")
    test1_one_to_many = ReferenceField("Test1", automatic_reference="test2_many_to_one")
    test1_many_to_one = ListField(ReferenceField("Test1"), automatic_reference="test2_one_to_many")
    test1_many_to_many = ListField(ReferenceField("Test1"), automatic_reference="test2_many_to_many")
