from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

from api.base.models import BaseModel, TimestampedMixin


class _EmailField(models.EmailField):
    def get_prep_value(self, value):
        return value if value else None


class User(BaseModel, TimestampedMixin, AbstractUser):
    """Default user in the app."""

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    objects = UserManager["User"]()

    email = _EmailField(
        verbose_name="email",
        unique=True,
        blank=True,
        null=True,
        default=None,
    )
