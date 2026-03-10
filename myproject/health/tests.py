from django.test import TestCase

# Create your tests here.


class HealthCheckTests(TestCase):
    def test_health_check_returns_ok(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
