from rest_framework.routers import DefaultRouter

from . import views

app_name = "issue"
router = DefaultRouter()

router.register(r'summary', views.SummaryViewSet, basename='summary')

urlpatterns = router.urls
