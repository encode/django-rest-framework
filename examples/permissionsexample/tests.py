from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.client import Client


class NaviguatePermissionsExamples(TestCase):
    """
    Sanity checks for permissions examples
    """

    def test_throttled_resource(self):
        url = reverse('throttled-resource')
        for i in range(0, 10):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 503)
        

    def test_loggedin_resource(self):
        url = reverse('loggedin-resource')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        loggedin_client = Client()
        loggedin_client.login(username='test', password='test')
        response = loggedin_client.get(url)
        self.assertEqual(response.status_code, 200)
