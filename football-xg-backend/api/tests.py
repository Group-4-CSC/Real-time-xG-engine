from django.test import SimpleTestCase
from rest_framework.test import APIClient


class HealthEndpointTests(SimpleTestCase):
    def test_health_endpoint_returns_ok(self):
        response = APIClient().get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class XGEndpointTests(SimpleTestCase):
    def test_calculate_xg_from_distance_and_angle(self):
        response = APIClient().post(
            "/api/xg/calculate/",
            {
                "distance_to_goal_m": 14,
                "angle_to_goal_deg": 25,
                "is_header": False,
                "is_penalty": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("xg", data)
        self.assertGreaterEqual(data["xg"], 0.0)
        self.assertLessEqual(data["xg"], 1.0)
        self.assertEqual(data["distance_to_goal_m"], 14)
        self.assertEqual(data["angle_to_goal_deg"], 25)
