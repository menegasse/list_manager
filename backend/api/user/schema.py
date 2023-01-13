from typing import Iterable, cast

from django.core.exceptions import ValidationError
from strawberry.types import Info
from strawberry_django_plus import gql

from api.list.models import List
from api.list.types import ListType

from .models import User
from .types import LogginInputType, UserType


@gql.type
class Query:
    @gql.django.field
    def me(self, info: Info) -> UserType | None:
        """The current logged-in user."""
        user = info.context.request.user
        if not user.is_authenticated or not user.is_active:
            return None

        return cast(UserType, user)

    @gql.connection
    def my_lists(self, info: Info) -> Iterable[ListType]:
        """The lists the user is participating in"""
        user = info.context.request.user

        lists = List.objects.filter(participants__in=user).order_by("created_at")

        return cast(Iterable[ListType], lists)

    def loggin(self, input: LogginInputType) -> UserType | None:
        """Login to the api"""
        try:
            user = User.objects.get(**input.__dict__)
            return cast(UserType, user)
        except User.DoesNotExist:
            return None


@gql.type
class Mutation:
    @gql.mutation
    def create_user(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        confirm_password: str,
    ) -> UserType:

        if password != confirm_password:
            raise ValidationError("Password confirmation does not match!")

        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists!")

        user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

        user.set_password(password)
        user.save()

        return cast(UserType, user)
