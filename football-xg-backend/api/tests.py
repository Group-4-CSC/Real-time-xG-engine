from Analytics.xg_model import compute_xg as analytics_compute_xg
from django.conf import settings
from django.test import SimpleTestCase
from rest_framework.test import APIClient
from unittest.mock import Mock, patch
from urllib.error import HTTPError
import json


class HealthEndpointTests(SimpleTestCase):
    def test_health_endpoint_returns_ok(self):
        response = APIClient().get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_frontend_origin_is_allowed_by_cors(self):
        response = APIClient().get(
            "/api/health/", HTTP_ORIGIN="http://localhost:5173"
        )

        self.assertEqual(
            response.headers["Access-Control-Allow-Origin"],
            "http://localhost:5173",
        )


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
        self.assertEqual(
            data["xg"],
            round(
                analytics_compute_xg(
                    {
                        "x": 85,
                        "y": 50,
                        "body_part": "right_foot",
                        "outcome": "goal",
                    }
                ),
                4,
            ),
        )

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

    def test_shot_outside_penalty_area_is_unsupported(self):
        response = APIClient().post(
            "/api/xg/calculate/",
            {"x": 80, "y": 50, "body_part": "right_foot", "outcome": "goal"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"xg": None, "xg_status": "unsupported"}
        )

    def test_shot_at_goalpost_is_unsupported(self):
        lower_post_y = (34 - 3.66) / 68 * 100
        response = APIClient().post(
            "/api/xg/calculate/",
            {
                "x": 100,
                "y": lower_post_y,
                "body_part": "right_foot",
                "outcome": "goal",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"xg": None, "xg_status": "unsupported"}
        )

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
        near_shot = {"x": 97, "y": 50, "body_part": "right_foot", "outcome": "goal"}
        same_shot_saved = {**near_shot, "outcome": "saved"}
        far_shot = {**near_shot, "x": 85}
        statsbomb_reference = {**near_shot, "statsbomb_xg": 0.99}

        goal_response = client.post("/api/xg/calculate/", near_shot, format="json")
        saved_response = client.post("/api/xg/calculate/", same_shot_saved, format="json")
        far_response = client.post("/api/xg/calculate/", far_shot, format="json")
        reference_response = client.post(
            "/api/xg/calculate/", statsbomb_reference, format="json"
        )

        self.assertEqual(goal_response.json()["xg"], saved_response.json()["xg"])
        self.assertEqual(goal_response.json()["xg"], reference_response.json()["xg"])
        self.assertGreater(goal_response.json()["xg"], far_response.json()["xg"])


class MatchSummaryEndpointTests(SimpleTestCase):
    metrics = {
        "home_score": 2,
        "away_score": 1,
        "home_shots": 12,
        "away_shots": 7,
        "home_xg": 1.72,
        "away_xg": 0.81,
    }

    def post_summary(self):
        return APIClient().post(
            "/api/match-summary/",
            self.metrics,
            format="json",
        )

    @staticmethod
    def provider_response(content):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = json.dumps(
            {"choices": [{"message": {"content": content}}]}
        ).encode("utf-8")
        return response

    @patch.object(settings, "OPENAI_API_KEY", "")
    def test_missing_api_key_returns_unavailable(self):
        with patch("api.llm.urlopen") as urlopen:
            response = self.post_summary()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"summary": None, "summary_status": "unavailable"},
        )
        urlopen.assert_not_called()

    @patch.object(settings, "OPENAI_API_KEY", "test-key")
    @patch("api.llm.urlopen", side_effect=TimeoutError("request timed out"))
    def test_provider_timeout_returns_unavailable(self, urlopen):
        response = self.post_summary()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["summary_status"], "unavailable")
        urlopen.assert_called_once()

    @patch.object(settings, "OPENAI_API_KEY", "test-key")
    @patch(
        "api.llm.urlopen",
        side_effect=HTTPError(
            "https://provider.invalid/chat", 503, "unavailable", {}, None
        ),
    )
    def test_provider_error_returns_unavailable(self, urlopen):
        response = self.post_summary()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["summary_status"], "unavailable")
        urlopen.assert_called_once()

    @patch.object(settings, "OPENAI_API_KEY", "test-key")
    def test_invalid_provider_output_returns_unavailable(self):
        valid = {
            "summary": (
                "The home side created stronger chances and converted them "
                "more often, while the away side remained competitive."
            ),
            "facts": self.metrics,
            "comparisons": {"score": "home", "shots": "home", "xg": "home"},
        }
        invalid_outputs = [
            {**valid, "facts": {**self.metrics, "home_score": 9}},
            {
                **valid,
                "comparisons": {
                    "score": "away",
                    "shots": "home",
                    "xg": "home",
                },
            },
            {
                **valid,
                "summary": (
                    "The home side scored twice despite creating weaker chances."
                ),
            },
        ]

        for output in invalid_outputs:
            with self.subTest(output=output):
                with patch(
                    "api.llm.urlopen",
                    return_value=self.provider_response(json.dumps(output)),
                ):
                    response = self.post_summary()

                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.json()["summary_status"], "unavailable"
                )

    @patch.object(settings, "OPENAI_API_KEY", "test-key")
    def test_valid_provider_output_returns_checked_summary(self):
        content = json.dumps(
            {
                "summary": (
                    "The home side created stronger chances and converted them "
                    "more often, while the away side remained competitive."
                ),
                "facts": self.metrics,
                "comparisons": {"score": "home", "shots": "home", "xg": "home"},
            }
        )
        with patch(
            "api.llm.urlopen", return_value=self.provider_response(content)
        ) as urlopen:
            response = self.post_summary()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["summary_status"], "generated")
        self.assertTrue(response.json()["summary"].startswith("The home side"))
        provider_request = urlopen.call_args.args[0]
        provider_payload = json.loads(provider_request.data.decode("utf-8"))
        numeric_payload = json.loads(provider_payload["messages"][1]["content"])
        self.assertEqual(numeric_payload, self.metrics)

    def test_match_summary_rejects_non_numeric_and_invalid_metrics(self):
        invalid_payloads = [
            {**self.metrics, "home_score": "two"},
            {**self.metrics, "home_xg": -0.1},
            {key: value for key, value in self.metrics.items() if key != "away_shots"},
        ]

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = APIClient().post(
                    "/api/match-summary/", payload, format="json"
                )
                self.assertEqual(response.status_code, 400)
