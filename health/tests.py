from django.test import TestCase


class HealthRequestSourceMiddlewareTests(TestCase):
    def test_logs_source_metadata_for_health_requests(self):
        with self.assertLogs("health.middleware", level="WARNING") as captured:
            response = self.client.get(
                "/health",
                REMOTE_ADDR="192.0.2.10",
                HTTP_USER_AGENT="Local monitor",
                HTTP_REFERER="http://localhost/status",
            )

        self.assertEqual(response.status_code, 404)
        self.assertIn("ip=192.0.2.10", captured.output[0])
        self.assertIn("user_agent='Local monitor'", captured.output[0])
        self.assertIn("referer='http://localhost/status'", captured.output[0])

    def test_does_not_log_other_paths(self):
        with self.assertNoLogs("health.middleware", level="WARNING"):
            self.client.get("/api/health/")
