from django.conf.urls import include, url
from rest_framework import routers
from test_read_only_default import ExampleViewSet

router = routers.DefaultRouter()
router.register(r'example', ExampleViewSet)

urlpatterns = [
    url('', include(router.urls)),
    url('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]