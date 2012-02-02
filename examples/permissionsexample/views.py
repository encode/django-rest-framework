from djangorestframework.views import View
from djangorestframework.permissions import PerUserThrottling, IsAuthenticated
from django.core.urlresolvers import reverse


class PermissionsExampleView(View):
    """
    A container view for permissions examples.
    """

    def get(self, request):
        return [
            {
                'name': 'Throttling Example',
                'url': reverse('throttled-resource')
            },
            {
                'name': 'Logged in example',
                'url': reverse('loggedin-resource')
            },
        ]


class ThrottlingExampleView(View):
    """
    A basic read-only View that has a **per-user throttle** of 10 requests per minute.

    If a user exceeds the 10 requests limit within a period of one minute, the
    throttle will be applied until 60 seconds have passed since the first request.
    """

    permissions = (PerUserThrottling,)
    throttle = '10/min'

    def get(self, request):
        """
        Handle GET requests.
        """
        return "Successful response to GET request because throttle is not yet active."


class LoggedInExampleView(View):
    """
    You can login with **'test', 'test'.** or use curl:

    `curl -X GET -H 'Accept: application/json' -u test:test http://localhost:8000/permissions-example`
    """

    permissions = (IsAuthenticated, )

    def get(self, request):
        return 'You have permission to view this resource'
