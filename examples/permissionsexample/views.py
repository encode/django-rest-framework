from djangorestframework.views import View
from djangorestframework.permissions import PerUserThrottling


class ThrottlingExampleView(View):
    """
    A basic read-only View that has a **per-user throttle** of 10 requests per minute.
    
    If a user exceeds the 10 requests limit within a period of one minute, the
    throttle will be applied until 60 seconds have passed since the first request.
    """
    
    permissions = ( PerUserThrottling, )
    throttle = '10/min'
    
    def get(self, request):
        """
        Handle GET requests.
        """
        return "Successful response to GET request because throttle is not yet active."