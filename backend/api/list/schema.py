from typing import cast

from strawberry.types import Info
from strawberry_django_plus import gql

from api.user.models import User
from api.user.types import UserType

from .models import List
from .types import (
    ListInputType,
    ListParticipantInputType,
    ListType,
    PromoveParticipantInputType,
)

_ListTypeOrNone = ListType | None


@gql.type
class Query:
    list: ListType = gql.django.node()


@gql.type
class Mutation:
    @gql.mutation
    def create_list(self, info: Info, input: ListInputType) -> _ListTypeOrNone:
        user = info.context.request.user

        if not user.is_authenticated or not user.is_active:
            return None

        list = List.objects.create(**input.__dict__, owner=user)
        return cast(ListType, list)

    @gql.mutation
    def add_participant(self, info: Info, input: ListParticipantInputType) -> _ListTypeOrNone:
        user = info.context.request.user
        list = cast(List, ListType.resolve_node(input.list_id.node_id))

        if any(user.has_perm(perm, list) for perm in ["list.owner", "list.admin"]):
            participant = cast(User, UserType.resolve_node(input.participant_id.node_id))
            list.add_participant(participant)

            return cast(ListType, list)
        else:
            raise PermissionError("You are not allowed to add participants!")

    @gql.mutation
    def remove_participant(self, info: Info, input: ListParticipantInputType) -> _ListTypeOrNone:
        user = info.context.request.user
        list = cast(List, ListType.resolve_node(input.list_id.node_id))

        if any(user.has_perm(perm, list) for perm in ["list.owner", "list.admin"]):
            participant = cast(User, UserType.resolve_node(input.participant_id.node_id))
            list.remove_participant(participant)

            return cast(ListType, list)

        raise PermissionError("You are not allowed to remove participants!")

    @gql.mutation
    def promove_to_admin(self, info: Info, input: PromoveParticipantInputType) -> _ListTypeOrNone:
        user = info.context.request.user
        list = cast(List, ListType.resolve_node(input.list_id.node_id))

        if any(user.has_perm(perm, list) for perm in ["list.owner", "list.admin"]):
            participant = cast(User, UserType.resolve_node(input.participant_id.node_id))
            list.promove_to_admin(participant)
