import contextlib
from typing import Any

from guardian.shortcuts import assign_perm
import pytest

from api.tests.base import GqlTestClient
from api.tests.utils import no_chached_user_perm as no_chace_perm
from api.user.models import User


@pytest.fixture(autouse=True)
@pytest.mark.django_db(transaction=True)
def _enable_db(db):
    from api.schemas import schema

    assert schema  # flake8'


@pytest.fixture
def gql_client(client):
    yield GqlTestClient(client)


@pytest.fixture
def no_chached_assign_perm():
    @contextlib.contextmanager
    @no_chace_perm
    def func(permissions: str | list[str], user: User, obj: Any):
        permissions = [permissions] if isinstance(permissions, str) else permissions

        for perm in permissions:
            assign_perm(perm, user, obj)

        yield

    return func
