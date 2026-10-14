from django.test import SimpleTestCase
from rest_framework.test import APIClient
from unittest.mock import patch


class HealthEndpointTests(SimpleTestCase):
    def test_health_endpoint_returns_ok(self):
        response = APIClient().get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class XGEndpointTests(SimpleTestCase):
    def test_calculate_xg_from_shared_shot_format(self):
        response = APIClient().post(
            "/api/xg/calculate/",
            {
                "x": 85,
                "y": 50,
                "body_part": "right_foot",
                "outcome": "goal",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("xg", data)
        self.assertGreaterEqual(data["xg"], 0.0)
        self.assertLessEqual(data["xg"], 1.0)
        self.assertEqual(data["xg_status"], "computed")

    @patch("api.views.compute_xg", return_value=None)
    def test_unsupported_shot_returns_null_xg_without_crashing(self, compute_xg):
        response = APIClient().post(
            "/api/xg/calculate/",
            {
                "x": 85,
                "y": 50,
                "body_part": "right_foot",
                "outcome": "goal",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"xg": None, "xg_status": "unsupported"}
        )
        compute_xg.assert_called_once()

    def test_rejects_missing_or_invalid_shot_fields(self):
        client = APIClient()
        invalid_shots = [
            {"x": 85, "y": 50, "body_part": "right_foot"},
            {"x": 101, "y": 50, "body_part": "right_foot", "outcome": "goal"},
            {"x": 85, "y": 50, "body_part": "right_foot", "outcome": "unknown"},
        ]

        for shot in invalid_shots:
            with self.subTest(shot=shot):
                response = client.post("/api/xg/calculate/", shot, format="json")
                self.assertEqual(response.status_code, 400)

    def test_xg_uses_shot_features_but_not_outcome(self):
        client = APIClient()
        near_shot = {"x": 85, "y": 50, "body_part": "right_foot", "outcome": "goal"}
        same_shot_saved = {**near_shot, "outcome": "saved"}
        far_shot = {**near_shot, "x": 40}

        goal_response = client.post("/api/xg/calculate/", near_shot, format="json")
        saved_response = client.post("/api/xg/calculate/", same_shot_saved, format="json")
        far_response = client.post("/api/xg/calculate/", far_shot, format="json")

        self.assertEqual(goal_response.json()["xg"], saved_response.json()["xg"])
        self.assertGreater(goal_response.json()["xg"], far_response.json()["xg"])
