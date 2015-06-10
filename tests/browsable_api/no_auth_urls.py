from __future__ import unicode_literals

from .views import MockView

urlpatterns = [
    (r'^$', MockView.as_view()),
]
