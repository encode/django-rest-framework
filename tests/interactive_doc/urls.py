from django.conf.urls import include, url

from rest_framework.documentation import include_docs_urls
from rest_framework.routers import DefaultRouter

from .data import DummyViewSet


router = DefaultRouter()

router.register(r'dummy/aaaas', DummyViewSet)
router.register(r'dummy/bbbbs', DummyViewSet)
router.register(r'not_dummies', DummyViewSet)

urlpatterns = [
    url(r'', include(router.urls)),
    url(r'^docs/', include_docs_urls())
]
