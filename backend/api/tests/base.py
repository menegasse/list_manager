import contextlib
import re
from typing import Any

from django.db import models
from strawberry.test import BaseGraphQLTestClient
from strawberry.test.client import Response
from strawberry_django_plus.relay import from_base64

from api.user.models import User


def _camelcase2snakecase(str_camel_case: str) -> str:
    str_snake_case = re.sub("([A-Z]+)", r"_\1", str_camel_case).lower()
    return str_snake_case[1:] if str_snake_case[0] == "_" else str_snake_case


class GqlTestClient(BaseGraphQLTestClient):
    def request(
        self,
        body: dict[str, object],
        headers: dict[str, object] | None = None,
        files: dict[str, object] | None = None,
    ):
        path = "/api/graphql/"

        kwargs: dict[str, object] = {"data": body}
        if files:
            kwargs["format"] = "multipart"
        else:
            kwargs["content_type"] = "application/json"

        return self._client.post(path, **kwargs)

    def query(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        fragments: str = "",
        headers: dict[str, object] | None = None,
        asserts_errors: bool = True,
        files: dict[str, object] | None = None,
    ) -> Response:
        body = self._build_body(fragments + query, variables, files)

        resp = self.request(body, headers, files)
        data = self._decode(resp, type="multipart" if files else "json")

        response = Response(
            errors=data.get("errors"),
            data=data.get("data"),
            extensions=data.get("extensions"),
        )
        if asserts_errors:
            print(response.errors)
            assert response.errors is None

        return response

    @contextlib.contextmanager
    def login(self, user: User):
        self._client.force_login(user)
        yield
        self._client.logout()


class BaseTest:
    def assert_created_object_model(
        self,
        model_type: type[models.Model],
        input_variables: dict[str, Any],
        response: Response,
    ) -> None:
        assert response.data and len(response.data) == 1
        data = response.data[next(iter(response.data))]

        assert isinstance(data, dict)
        _, obj_id = from_base64(data.get("id"))

        assert isinstance(obj_id, str)
        obj = model_type.objects.get(pk=obj_id)

        variables = input_variables.get("input", input_variables)
        for k, v in variables.items():
            if k == "id":
                continue
            assert getattr(obj, _camelcase2snakecase(k)) == v

    def assert_response_errors(self, response: Response, messages: list[str]):
        assert response.errors is not None
        assert {error["message"] for error in response.errors} == set(messages)
