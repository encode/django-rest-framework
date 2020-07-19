from django.urls import include, path

from .views import MockView

urlpatterns = [
    path('', MockView.as_view()),
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]
