from typing import Generic, TypeVar

from django.contrib.auth.hashers import make_password
import factory

from api.list.models import List, ListItem
from api.user.models import User

_T = TypeVar("_T")
factory.Faker._DEFAULT_LOCALE = "pt_BR"


class _BaseFactory(Generic[_T], factory.Factory):
    @classmethod
    def create(cls, **kwargs) -> _T:
        return super().create(**kwargs)

    @classmethod
    def create_batch(cls, size: int, **kwargs) -> list[_T]:
        return super().create_batch(size, **kwargs)


class _BaseDjangoFactory(factory.django.DjangoModelFactory, _BaseFactory[_T]):
    ...


class _BaseDictFactory(factory.DictFactory, _BaseFactory[_T]):
    ...


class UserFactory(_BaseDjangoFactory[User]):
    class Meta:
        model = User

    username = factory.Faker("username")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    username = factory.Faker("email")
    password = factory.LazyFunction(lambda: make_password("foobar"))
    is_active = True


class ListFactory(_BaseDjangoFactory[List]):
    class Meta:
        model = List

    title = factory.Sequence(lambda n: f"List {n}")
    owner = factory.SubFactory(UserFactory)
    description = factory.LazyAttribute(lambda l: f"List: {l.title} do usuário: {l.owner}")
    is_active = True
    is_public = True


class ListItemFactory(_BaseDjangoFactory[ListItem]):
    class Meta:
        model = ListItem

    name = factory.Sequence(lambda n: f"Item {n}")
    quantity = 1
    user = factory.SubFactory(UserFactory)
    list = factory.SubFactory(ListFactory)
    value = None
    weight = None
    is_active = True
