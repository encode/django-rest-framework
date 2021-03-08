from django.urls import path

from .views import MockView

urlpatterns = [
    path('', MockView.as_view()),
]
