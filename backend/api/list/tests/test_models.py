import decimal

from django.forms import ValidationError
import pytest

from api.list.models import List
from api.tests.faker import ListFactory, ListItemFactory, UserFactory
from api.tests.utils import no_chached_user_perm


class TestList:
    @no_chached_user_perm
    def test_owner_list(self):
        user = UserFactory.create()
        list = ListFactory.create(owner=user)
        assert user.has_perm("owner", list)

    @no_chached_user_perm
    def test_add_participant(self):
        list = ListFactory.create()
        user = UserFactory.create()
        assert not user.has_perm("list.participant", list)

        list.add_participant(user)
        list_update = List.objects.get(pk=list.pk)
        assert user in list_update.participants.all()
        assert user.has_perm("list.participant", list)

    @no_chached_user_perm
    def test_user_is_arealy_paticipant(self):
        list = ListFactory.create()
        user = UserFactory.create()
        list.add_participant(user)
        assert user.has_perm("list.participant", list)

        with pytest.raises(ValidationError) as e:
            list.add_participant(user)

        assert e.value.message == "User is already a participant of this list!"
        assert user.has_perm("list.participant", list)

    @no_chached_user_perm
    def test_remove_participant(self):
        user = UserFactory.create()

        list1 = ListFactory.create()
        list2 = ListFactory.create()

        for list in [list1, list2]:
            list.add_participant(user)
            assert user.has_perm("list.participant", list)

        list1.remove_participant(user)
        assert user not in list1.participants.all()
        for perm, _ in list1.__class__._meta.permissions:
            assert not user.has_perm("list.participant", list1)

        assert user in list2.participants.all()
        assert user.has_perm("list.participant", list2)

    @no_chached_user_perm
    def test_remove_no_user_participant(self):
        user = UserFactory.create()
        list = ListFactory.create()

        with pytest.raises(ValidationError) as e:
            list.remove_participant(user)
        assert e.value.message == "User doesn't participate of this list!"

        for perm, _ in list.__class__._meta.permissions:
            assert not user.has_perm(perm, list)

    @no_chached_user_perm
    def test_promove_participant_to_admin(self):
        user = UserFactory.create()
        list = ListFactory.create()
        list.add_participant(user)

        list.promove_to_admin(user)
        assert user.has_perm("list.admin", list)

    @no_chached_user_perm
    def test_promove_participant_is_arealy_admin(self):
        user = UserFactory.create()
        list = ListFactory.create()
        list.add_participant(user)
        list.promove_to_admin(user)
        assert user.has_perm("list.admin", list)

    @no_chached_user_perm
    def test_promove_no_participant_to_admin(self):
        user = UserFactory.create()
        list = ListFactory.create()

        assert not user.has_perm("list.participant", list)
        assert not user.has_perm("list.admin", list)
        with pytest.raises(ValidationError) as e:
            list.promove_to_admin(user)
        assert e.value.message == "User doesn't participate of this list!"

    def test_add_item(self):
        list = ListFactory.create()

        items = set(list.add_item("Item {i}") for i in range(6))
        assert items == set(list.items.all())

    def test_remove_items(self):
        list = ListFactory.create()
        items = ListItemFactory.create_batch(5, list=list)

        list.remove_items([items[0], items[4]])
        list.remove_items(items[1])
        assert set(items) - set([items[0], items[4], items[1]]) == set(
            list.items.filter(is_active=True)
        )

    def test_subtotal(self):
        list = ListFactory.create()
        ListItemFactory.create(value=decimal.Decimal("5.00"), quantity=2, list=list)
        ListItemFactory.create(value=decimal.Decimal("10.00"), list=list)
        ListItemFactory.create(value=None, list=list)

        assert list.subtotal == decimal.Decimal("20.00")

    def test_reserve(self):
        list = ListFactory.create(threshold=decimal.Decimal("100.00"))
        ListItemFactory.create_batch(
            size=3,
            value=decimal.Decimal("5.00"),
            quantity=2,
            list=list,
        )
        assert list.reserve == decimal.Decimal("70.00")


class TestListItem:
    def test_total(self):
        item = ListItemFactory.create(quantity=2, value=decimal.Decimal("5.00"))
        assert item.total == decimal.Decimal("10.00")
