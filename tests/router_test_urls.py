from django.conf.urls import url, include

from rest_framework import viewsets, mixins, routers

from .test_routers import APIRootTestModel


class APIRootTestViewSet(viewsets.ModelViewSet):
    model = APIRootTestModel


class ListlessViewSet(mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    model = APIRootTestModel


router = routers.DefaultRouter()
router.register(r'test-model', APIRootTestViewSet)


listless_router = routers.DefaultRouter()
# Avoid conflict with the api/ route.
listless_router.root_view_name = 'listless-api-root'
listless_router.register(r'full', APIRootTestViewSet, 'full')
listless_router.register(r'listless', ListlessViewSet, 'listless')


urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^namespaced-api/', include(router.urls, namespace='api-namespace')),
    url(r'^listless/', include(listless_router.urls)),
]
