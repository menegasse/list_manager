import decimal
from typing import TYPE_CHECKING, Any

from django.db import models
from django.forms import ValidationError
from guardian.shortcuts import assign_perm, remove_perm

from api.base import hooks
from api.base.models import BaseModel, TimestampedMixin
from api.user.models import User

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager


class List(BaseModel, TimestampedMixin):
    """List model"""

    class Meta:
        permissions = [
            ("owner", "Owner"),
            ("admin", "Admin"),
            ("participant", "Participant"),
        ]
        verbose_name = "list"
        verbose_name_plural = "lists"

    items: "RelatedManager[ListItem]"

    title = models.CharField(
        verbose_name="Name",
        max_length=58,
    )
    owner = models.ForeignKey[User](
        User,
        on_delete=models.CASCADE,
        verbose_name="owner",
        related_name="owner",
        related_query_name="owner",
        db_index=True,
    )
    participants = models.ManyToManyField[User, Any](User)
    description = models.TextField(
        verbose_name="Description",
        max_length=255,
        blank=True,
        default=None,
    )
    is_active = models.BooleanField(
        verbose_name="is_active",
        blank=True,
        default=True,
    )
    is_public = models.BooleanField(
        verbose_name="is_public",
        blank=True,
        default=True,
    )
    threshold = models.DecimalField(
        verbose_name="Threshold Value",
        help_text="What is the total threshold value of the list items?",
        max_digits=20,
        decimal_places=2,
        null=True,
        default=None,
        blank=True,
    )

    #
    #   Private
    #

    def __repr__(self) -> str:
        return f"List: ({self.title})"

    #
    #  Hooks
    #

    @hooks.post_save(on_commit=True)
    def post_save(self, created: bool, **kwargs):
        if created:
            self.participants.add(self.owner)
            assign_perm("owner", self.owner, self)

    #
    # Publics
    #

    def add_participant(self, user: User):
        """Add new participant to the list"""
        if user.has_perm("list.participant", self):
            raise ValidationError("User is already a participant of this list!")

        self.participants.add(user)
        assign_perm("list.participant", user, self)

    def remove_participant(self, user: User):
        """Remove the participant from the list including all their permissions"""
        if not user.has_perm("list.participant", self):
            raise ValidationError("User doesn't participate of this list!")

        self.participants.remove(user)
        for perm, _ in List._meta.permissions:
            remove_perm(perm, user, self)

    def promove_to_admin(self, user: User):
        """Promove a participant to admin"""
        if not user.has_perm("list.participant", self):
            raise ValidationError("User doesn't participate of this list!")

        if any(user.has_perms(perm, self) for perm in ["list.admin", "list.owner"]):
            raise ValidationError("User is already admin of this list!")

        assign_perm("admin", user, self)

    def add_item(
        self,
        name: str,
        /,
        *,
        quantity: int = 1,
        user: User | None = None,
        value: decimal.Decimal | None = None,
        weight: decimal.Decimal | None = None,
    ) -> "ListItem":
        return ListItem.objects.create(
            name=name,
            list=self,
            is_active=True,
            quantity=quantity,
            user=user,
            value=value,
            weight=weight,
        )

    def remove_items(self, items: "ListItem | list[ListItem]") -> bool:
        if isinstance(items, ListItem):
            items = [items]

        return ListItem.objects.filter(list=self, pk__in=[item.pk for item in items]).update(
            is_active=False,
        ) == len(items)

    #
    # Property
    #

    @property
    def subtotal(self) -> decimal.Decimal:
        return decimal.Decimal(sum(item.total for item in self.items.filter(is_active=True)))

    @property
    def reserve(self) -> decimal.Decimal | None:
        return self.threshold and self.threshold - self.subtotal


class ListItem(BaseModel, TimestampedMixin):
    """List item model"""

    class Meta:
        verbose_name = "item"
        verbose_name_plural = "items"

    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
    )
    quantity = models.IntegerField(
        verbose_name="Quantity",
        default=1,
    )
    user_id: int | None
    user = models.ForeignKey[User | None](
        User,
        on_delete=models.PROTECT,
        verbose_name="user",
        related_name="users",
        related_query_name="user",
        db_index=True,
        default=None,
        blank=True,
        null=True,
    )
    list = models.ForeignKey[List](
        List,
        on_delete=models.CASCADE,
        verbose_name="list",
        related_name="items",
        related_query_name="item",
        db_index=True,
    )
    value = models.DecimalField(
        verbose_name="Value",
        help_text="How much does the item cost?",
        max_digits=20,
        decimal_places=2,
        null=True,
        default=None,
        blank=True,
    )
    weight = models.DecimalField(
        verbose_name="Weight",
        help_text="Weight in g",
        max_digits=20,
        decimal_places=2,
        null=True,
        default=None,
        blank=True,
    )
    description = models.TextField(
        verbose_name="Description",
        max_length=255,
        blank=True,
        default="",
    )
    is_active = models.BooleanField(
        verbose_name="is_active",
        blank=True,
        default=True,
    )

    #
    # Property
    #

    @property
    def total(self) -> decimal.Decimal:
        return (self.value or decimal.Decimal(0)) * self.quantity
