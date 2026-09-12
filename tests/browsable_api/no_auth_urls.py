from django.urls import path

from .views import BasicModelWithUsersViewSet, MockView

urlpatterns = [
    path('', MockView.as_view()),
    path('basicviewset', BasicModelWithUsersViewSet.as_view({'get': 'list'})),
]
