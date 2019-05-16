from django.conf.urls import url

from .views import MockView

urlpatterns = [
    url(r'^$', MockView.as_view()),
]
