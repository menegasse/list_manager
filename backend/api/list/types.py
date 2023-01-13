import decimal

from strawberry_django_plus import gql

from api.list.models import List, ListItem
from api.user.types import UserType

#
# Input
#


@gql.input
class ListInputType:
    title: str
    description: str | None
    is_public: bool = True


@gql.input
class ListParticipantInputType:
    participant_id: gql.relay.GlobalID
    list_id: gql.relay.GlobalID


@gql.input
class PromoveParticipantInputType(ListParticipantInputType):
    permission: str


#
# Type
#


@gql.django.type(ListItem)
class ItemType(gql.Node):
    name: str
    description: str | None
    quantity: int | None
    value: decimal.Decimal | None
    weight: decimal.Decimal | None
    owner: UserType


@gql.django.type(List)
class ListType(gql.Node):
    title: str
    description: str | None
    is_public: bool | None
    owner: UserType
    participants: list[UserType | None]
    items: list[ItemType | None]
