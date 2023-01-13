import pytest
from strawberry_django_plus.relay import from_base64, to_base64

from api.list.models import List
from api.tests.base import BaseTest, GqlTestClient
from api.tests.faker import ListFactory, UserFactory
from api.user.models import User

_fragments = """\
fragment userFields on UserType {
    id
    username
    email
    isActive
}

fragment itemFields on ItemType {
    id
    name
    description
    quantity
    value
    weight
    owner{
        ...userFields
    }
}

fragment listFields on ListType {
    id
    title
    description
    owner{
        ...userFields
    }
    participants{
        ...userFields
    }
    items{
        ...itemFields
    }
    isPublic
}
"""


class TestMutation(BaseTest):
    def test_create_list(self, gql_client: GqlTestClient):
        mutation = """
            mutation TestCreateList($input: ListInputType!){
                createList(input: $input){
                    ...listFields
                }
            }
        """
        input_variables = {
            "input": {
                "title": "Supermarket",
                "description": "Month shopping",
                "isPublic": True,
            },
        }
        user = UserFactory.create()

        with gql_client.login(user):
            response = gql_client.query(mutation, fragments=_fragments, variables=input_variables)
            self.assert_created_object_model(List, input_variables, response)

    @pytest.mark.parametrize("permission", ["list.owner", "list.admin"])
    def test_add_new_participant(
        self,
        permission: str,
        gql_client: GqlTestClient,
        no_chached_assign_perm,
    ):
        mutation = """
            mutation TestAddParticipant($input: ListParticipantInputType!){
                addParticipant(input: $input){
                    ...listFields
                }
            }
        """

        user = UserFactory.create()
        list = ListFactory.create()

        with no_chached_assign_perm(permission, user, list):
            new_user = UserFactory.create()
            input_variables = {
                "input": {
                    "participantId": to_base64("UserType", new_user.id),
                    "listId": to_base64("ListTyper", list.id),
                },
            }

            with gql_client.login(user):
                response = gql_client.query(
                    mutation,
                    fragments=_fragments,
                    variables=input_variables,
                )
                assert response.data and response.data["addParticipant"]
                assert "ListType", str(list.id) == from_base64(
                    response.data["addParticipant"].pop("id")
                )

                participant_ids = [
                    from_base64(u["id"])[1]  # get participant id
                    for u in response.data["addParticipant"].pop("participants")
                ]
                participants_obj = set(User.objects.filter(pk__in=participant_ids))
                assert {list.owner, new_user} == participants_obj

    @pytest.mark.parametrize("permission", ["list.participant"])
    def test_no_permission_to_add_new_permission(
        self,
        permission: str,
        gql_client: GqlTestClient,
        no_chached_assign_perm,
    ):
        assert permission not in ["list.owner", "list.admin"]

        mutation = """
            mutation TestAddParticipant($input: ListParticipantInputType!){
                addParticipant(input: $input){
                    ...listFields
                }
            }
        """

        user = UserFactory.create()
        list = ListFactory.create()

        with no_chached_assign_perm(permission, user, list):
            participant = UserFactory.create()
            input_variables = {
                "input": {
                    "participantId": to_base64("UserType", participant.id),
                    "listId": to_base64("ListTyper", list.id),
                },
            }

            with gql_client.login(user):
                response = gql_client.query(
                    mutation,
                    fragments=_fragments,
                    variables=input_variables,
                    asserts_errors=False,
                )

                self.assert_response_errors(response, ["You are not allowed to add participants!"])

            assert participant not in list.participants.all()

    @pytest.mark.parametrize("permission", ["list.owner", "list.admin"])
    def test_remove_participant(
        self,
        permission: str,
        gql_client: GqlTestClient,
        no_chached_assign_perm,
    ):
        mutation = """
            mutation TestRemoveParticipant($input: ListParticipantInputType!){
                removeParticipant(input: $input){
                    ...listFields
                }
            }
        """

        user = UserFactory.create()
        list = ListFactory.create()

        participant = UserFactory.create()
        list.add_participant(participant)

        with no_chached_assign_perm(permission, user, list):
            input_variables = {
                "input": {
                    "participantId": to_base64("UserType", participant.id),
                    "listId": to_base64("ListTyper", list.id),
                },
            }

            with gql_client.login(user):
                response = gql_client.query(
                    mutation,
                    fragments=_fragments,
                    variables=input_variables,
                )
                assert response.data and response.data["removeParticipant"]
                assert "ListType", str(list.id) == from_base64(
                    response.data["removeParticipant"].pop("id")
                )
                assert all(not participant.has_perm(perm, list) for perm in List._meta.permissions)
