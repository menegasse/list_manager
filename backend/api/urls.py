# from django.conf import settings
from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.urls import path
from django.urls.resolvers import URLPattern, URLResolver
from strawberry.django.views import GraphQLView

from api.schemas import schema

urlpatterns: list[URLPattern | URLResolver] = [
    path("listmanager-admin/", admin.site.urls),
    path(
        "api/graphql/",
        GraphQLView.as_view(graphiql=settings.DEBUG, schema=schema),
    ),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
