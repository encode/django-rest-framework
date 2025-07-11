# handler404 and handler500 are needed for admin tests
from django.urls import path
from guardian.compat import handler404, handler500  # pyflakes:ignore
from guardian.mixins import PermissionRequiredMixin
from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.views.generic import View

admin.autodiscover()


class TestClassRedirectView(PermissionRequiredMixin, View):
    permission_required = 'testapp.change_project'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', LoginView.as_view(template_name='blank.html')),
    path('permission_required/', TestClassRedirectView.as_view()),
]
