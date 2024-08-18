from mongoengine import connect, Q

from wiederverwendbar.starlette_admin.mongoengine.auth.documents import Session, User


# connect to database
connect("test",
        host="localhost",
        port=27017)


# def search(document_type: type[Document], query: Union[None, dict, list[dict]] = None) -> list[Document]:
#     raw_query = {}
#     if query is None:
#         raw_query = {}
#     elif isinstance(query, dict):
#         raw_query = {"__raw__": query}
#     elif isinstance(query, list):
#         or_query = []
#         for q in query:
#             if len(q) == 0:
#                 continue
#             or_query.append(q)
#         if len(or_query) == 0:
#             raw_query = {}
#         elif len(or_query) == 1:
#             raw_query = {"__raw__": or_query[0]}
#         else:
#             raw_query = {"__raw__": {"$or": or_query}}
#     else:
#         raise ValueError("query must be None, dict or list of dict")
#
#     query_set = document_type.objects(**raw_query)
#
#     return list(query_set)


if __name__ == '__main__':
    # search_query1 = {"test_str": "test123"}
    # search_query2 = {"test_int123": {"$gt": 123}}
    #
    # objects = search(Test, [search_query1, search_query2])

    q = Q(**{"__raw__": {"user__name": "test"}})

    sessions = list(Session.objects().aggregate(
        {"$lookup": {
            "from": "auth.user",
            "foreignField": "_id",
            "localField": "user",
            "as": "result",
        }},
        {"$unwind": "$result"},
        {"$match": {"result.name": "test"}}))

    print()
