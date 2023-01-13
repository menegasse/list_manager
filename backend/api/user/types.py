from strawberry_django_plus import gql

from api.user.models import User


@gql.django.type(User)
class UserType(gql.Node):
    username: str
    email: str
    is_active: bool


@gql.type
class LogginInputType:
    email: str
    password: str
