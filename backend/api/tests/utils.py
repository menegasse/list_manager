from typing import Any
from unittest import mock

from guardian.shortcuts import get_perms

from api.user.models import User


def no_chached_user_perm(func):
    """Decorator to disable the user's permissions cache and
    check directly with the ones in the database"""

    def _user_has_perm(user: User, perm: str, obj: Any) -> bool:
        if "." in perm:
            _, perm = perm.split(".")

        return perm in get_perms(user, obj)

    def wrapper(*args, **kwargs):
        mock_module_perm_function = mock.patch(
            "guardian.backends.ObjectPermissionBackend.has_perm",
            side_effect=_user_has_perm,
        )

        with mock_module_perm_function:
            return func(*args, **kwargs)

    return wrapper
