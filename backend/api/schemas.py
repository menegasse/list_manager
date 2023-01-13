from strawberry import Schema
from strawberry.tools import merge_types

from api.list.schema import Mutation as ListMutation
from api.list.schema import Query as ListQuery
from api.user.schema import Mutation as UserMutation
from api.user.schema import Query as UserQuery

Query = merge_types(
    "Query",
    (
        UserQuery,
        ListQuery,
    ),
)
Mutation = merge_types(
    "Mutation",
    (
        UserMutation,
        ListMutation,
    ),
)


schema = Schema(
    query=Query,
    mutation=Mutation,
)
