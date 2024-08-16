from typing import Union

from mongoengine import connect, Document, StringField, IntField, FloatField, BooleanField, DictField


class Test(Document):
    meta = {"collection": "test"}

    test_str = StringField()
    test_int = IntField()
    test_float = FloatField()
    test_bool = BooleanField()
    test_dict = DictField()


# connect to database
connect("test",
        host="localhost",
        port=27017)


def search(document_type: type[Document], query: Union[None, dict, list[dict]] = None) -> list[Document]:
    raw_query = {}
    if query is None:
        raw_query = {}
    elif isinstance(query, dict):
        raw_query = {"__raw__": query}
    elif isinstance(query, list):
        or_query = []
        for q in query:
            if len(q) == 0:
                continue
            or_query.append(q)
        if len(or_query) == 0:
            raw_query = {}
        elif len(or_query) == 1:
            raw_query = {"__raw__": or_query[0]}
        else:
            raw_query = {"__raw__": {"$or": or_query}}
    else:
        raise ValueError("query must be None, dict or list of dict")

    query_set = document_type.objects(**raw_query)

    return list(query_set)


if __name__ == '__main__':
    search_query1 = {"test_str": "test123"}
    search_query2 = {"test_int123": {"$gt": 123}}

    objects = search(Test, [search_query1, search_query2])

    print()
