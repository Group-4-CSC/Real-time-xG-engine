
import io
import json
import os

from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from Analytics.xg_model import compute_xg as analytics_compute_xg
from django.test import SimpleTestCase
from rest_framework.test import APIClient


class HealthEndpointTests(SimpleTestCase):

    def test_health_endpoint_returns_ok(self):
        response = APIClient().get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_frontend_origin_is_allowed_by_cors(self):
        response = APIClient().get(
            "/api/health/",
            HTTP_ORIGIN="http://localhost:5173",
        )

        self.assertEqual(
            response.headers["Access-Control-Allow-Origin"],
            "http://localhost:5173",
        )


class XGEndpointTests(SimpleTestCase):

    def test_calculate_xg_from_shared_shot_format(self):
        shot = {
            "x": 85,
            "y": 50,
            "body_part": "right_foot",
            "outcome": "goal",
        }

        response = APIClient().post(
            "/api/xg/calculate/",
            shot,
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
            round(analytics_compute_xg(shot), 4),
        )

    @patch("api.views.compute_xg", return_value=None)
    def test_unsupported_shot_returns_null_xg_without_crashing(
        self, compute_xg
    ):
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
            response.json(),
            {"xg": None, "xg_status": "unsupported"},
        )

        compute_xg.assert_called_once()

    def test_shot_outside_penalty_area_is_unsupported(self):
        response = APIClient().post(
            "/api/xg/calculate/",
            {
                "x": 80,
                "y": 50,
                "body_part": "right_foot",
                "outcome": "goal",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {"xg": None, "xg_status": "unsupported"},
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
            response.json(),
            {"xg": None, "xg_status": "unsupported"},
        )

    def test_rejects_missing_or_invalid_shot_fields(self):
        client = APIClient()

        invalid_shots = [
            {
                "x": 85,
                "y": 50,
                "body_part": "right_foot",
            },
            {
                "x": 101,
                "y": 50,
                "body_part": "right_foot",
                "outcome": "goal",
            },
            {
                "x": 85,
                "y": 50,
                "body_part": "right_foot",
                "outcome": "unknown",
            },
        ]

        for shot in invalid_shots:
            with self.subTest(shot=shot):
                response = client.post(
                    "/api/xg/calculate/",
                    shot,
                    format="json",
                )

                self.assertEqual(response.status_code, 400)

    def test_xg_uses_shot_features_but_not_outcome(self):
        client = APIClient()

        near_shot = {
            "x": 97,
            "y": 50,
            "body_part": "right_foot",
            "outcome": "goal",
        }

        same_shot_saved = {
            **near_shot,
            "outcome": "saved",
        }

        far_shot = {
            **near_shot,
            "x": 85,
        }

        statsbomb_reference = {
            **near_shot,
            "statsbomb_xg": 0.99,
        }

        goal_response = client.post(
            "/api/xg/calculate/",
            near_shot,
            format="json",
        )

        saved_response = client.post(
            "/api/xg/calculate/",
            same_shot_saved,
            format="json",
        )

        far_response = client.post(
            "/api/xg/calculate/",
            far_shot,
            format="json",
        )

        reference_response = client.post(
            "/api/xg/calculate/",
            statsbomb_reference,
            format="json",
        )

        self.assertEqual(
            goal_response.json()["xg"],
            saved_response.json()["xg"],
        )

        self.assertEqual(
            goal_response.json()["xg"],
            reference_response.json()["xg"],
        )

        self.assertGreater(
            goal_response.json()["xg"],
            far_response.json()["xg"],
        )


class AIMatchSummaryEndpointTests(SimpleTestCase):

    def setUp(self):
        self.client = APIClient()

        self.url = "/api/ai/match-summary/"

        self.payload = {
            "match_id": "match-1",
            "half": "all",
            "teams": [
                {
                    "name": "Home",
                    "shots": 5,
                    "goals": 1,
                    "xg": 0.8,
                    "xg_calculated_shots": 5,
                    "xg_missing_shots": 0,
                },
                {
                    "name": "Away",
                    "shots": 3,
                    "goals": 0,
                    "xg": 0.4,
                    "xg_calculated_shots": 3,
                    "xg_missing_shots": 0,
                },
            ],
        }

        self.valid_summary = (
            "Home scored 1 goal from 5 shots. "
            "Away scored 0 goals from 3 shots. "
            "Home recorded 0.80 xG and Away recorded 0.40 xG."
        )

    def assert_fallback(self, response):
        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertTrue(data["is_fallback"])
        self.assertFalse(data["is_placeholder"])
        self.assertEqual(data["source"], "fallback")

        self.assertIn(
            "Home: 1 goals, 5 shots",
            data["summary"],
        )

        self.assertIn(
            "Away: 0 goals, 3 shots",
            data["summary"],
        )

    def provider_response(self, content):
        return io.BytesIO(
            json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": content,
                            }
                        }
                    ]
                }
            ).encode("utf-8")
        )

    @patch("api.views.generate_summary")
    def test_ai_match_summary_returns_generated_summary(
        self, mock_generate
    ):
        mock_generate.return_value = self.valid_summary

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json()["summary"],
            self.valid_summary,
        )

        self.assertFalse(
            response.json()["is_placeholder"]
        )

        self.assertFalse(
            response.json()["is_fallback"]
        )

        self.assertEqual(
            response.json()["source"],
            "ai",
        )

        mock_generate.assert_called_once()

    @patch(
        "api.views.generate_summary",
        side_effect=RuntimeError("AI unavailable"),
    )
    def test_backend_returns_safe_fallback(
        self, mock_generate
    ):
        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assert_fallback(response)

    @patch(
        "api.views.generate_summary",
        side_effect=RuntimeError("AI unavailable"),
    )
    def test_fallback_preserves_unknown_xg(
        self, mock_generate
    ):
        self.payload["teams"][0]["xg"] = None
        self.payload["teams"][0]["xg_calculated_shots"] = 0
        self.payload["teams"][0]["xg_missing_shots"] = 5

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assert_fallback(response)

        self.assertIn(
            "xG is unavailable",
            response.json()["summary"],
        )

        self.assertNotIn(
            "Home: 1 goals, 5 shots, xG is 0.00",
            response.json()["summary"],
        )

    @patch(
        "api.views.generate_summary",
        side_effect=RuntimeError("AI unavailable"),
    )
    def test_fallback_discloses_partial_xg(
        self, mock_generate
    ):
        self.payload["teams"][0]["xg_calculated_shots"] = 3
        self.payload["teams"][0]["xg_missing_shots"] = 2

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assert_fallback(response)

        self.assertIn(
            "incomplete xG data",
            response.json()["summary"],
        )

    @patch("api.ai_summary.urlopen")
    def test_missing_api_key_returns_fallback(
        self, mock_urlopen
    ):
        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": ""},
        ):
            response = self.client.post(
                self.url,
                self.payload,
                format="json",
            )

        self.assert_fallback(response)
        mock_urlopen.assert_not_called()

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "mock-test-key"},
    )
    @patch("api.ai_summary.urlopen")
    def test_runtime_uses_versioned_prompt(
        self, mock_urlopen
    ):
        mock_urlopen.return_value = self.provider_response(
            self.valid_summary
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            response.json()["is_fallback"]
        )

        self.assertEqual(
            response.json()["summary"],
            self.valid_summary,
        )

        mock_urlopen.assert_called_once()

        request = mock_urlopen.call_args.args[0]

        sent_payload = json.loads(
            request.data.decode("utf-8")
        )

        prompt_path = (
            Path(__file__).resolve().parents[2]
            / "prompts"
            / "match_summary_v1.txt"
        )

        expected_prompt = prompt_path.read_text(
            encoding="utf-8"
        )

        self.assertEqual(
            sent_payload["messages"][0]["content"],
            expected_prompt,
        )

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "mock-test-key"},
    )
    @patch("api.ai_summary.urlopen")
    def test_http_error_returns_fallback(
        self, mock_urlopen
    ):
        mock_urlopen.side_effect = HTTPError(
            "https://api.openai.com",
            503,
            "Service unavailable",
            None,
            None,
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assert_fallback(response)
        mock_urlopen.assert_called_once()

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "mock-test-key"},
    )
    @patch("api.ai_summary.urlopen")
    def test_url_error_returns_fallback(
        self, mock_urlopen
    ):
        mock_urlopen.side_effect = URLError(
            "Connection failed"
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assert_fallback(response)
        mock_urlopen.assert_called_once()

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "mock-test-key"},
    )
    @patch("api.ai_summary.urlopen")
    def test_timeout_returns_fallback(
        self, mock_urlopen
    ):
        mock_urlopen.side_effect = TimeoutError(
            "Request timed out"
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assert_fallback(response)
        mock_urlopen.assert_called_once()

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "mock-test-key"},
    )
    @patch("api.ai_summary.urlopen")
    def test_malformed_json_returns_fallback(
        self, mock_urlopen
    ):
        mock_urlopen.return_value = io.BytesIO(
            b"invalid json"
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assert_fallback(response)
        mock_urlopen.assert_called_once()

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "mock-test-key"},
    )
    @patch("api.ai_summary.urlopen")
    def test_missing_choices_returns_fallback(
        self, mock_urlopen
    ):
        mock_urlopen.return_value = io.BytesIO(
            b"{}"
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assert_fallback(response)

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "mock-test-key"},
    )
    @patch("api.ai_summary.urlopen")
    def test_missing_content_returns_fallback(
        self, mock_urlopen
    ):
        mock_urlopen.return_value = io.BytesIO(
            b'{"choices":[{"message":{}}]}'
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assert_fallback(response)

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "mock-test-key"},
    )
    @patch("api.ai_summary.urlopen")
    def test_null_content_returns_fallback(
        self, mock_urlopen
    ):
        mock_urlopen.return_value = self.provider_response(
            None
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assert_fallback(response)

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "mock-test-key"},
    )
    @patch("api.ai_summary.urlopen")
    def test_empty_content_returns_fallback(
        self, mock_urlopen
    ):
        mock_urlopen.return_value = self.provider_response(
            ""
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assert_fallback(response)

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "mock-test-key"},
    )
    @patch("api.ai_summary.urlopen")
    def test_hallucinated_number_returns_fallback(
        self, mock_urlopen
    ):
        mock_urlopen.return_value = self.provider_response(
            "Home scored 99 goals. "
            "Away scored 0 goals. "
            "Home recorded 0.80 xG."
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assert_fallback(response)

        self.assertNotIn(
            "99 goals",
            response.json()["summary"],
        )

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "mock-test-key"},
    )
    @patch("api.ai_summary.urlopen")
    def test_invalid_summary_length_returns_fallback(
        self, mock_urlopen
    ):
        mock_urlopen.return_value = self.provider_response(
            "Home scored 1 goal."
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assert_fallback(response)

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "mock-test-key"},
    )
    @patch("api.ai_summary.urlopen")
    def test_missing_partial_xg_warning_returns_fallback(
        self, mock_urlopen
    ):
        self.payload["teams"][0]["xg_calculated_shots"] = 3
        self.payload["teams"][0]["xg_missing_shots"] = 2

        mock_urlopen.return_value = self.provider_response(
            self.valid_summary
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assert_fallback(response)

    @patch("api.views.generate_summary")
    def test_invalid_match_statistics_are_rejected(
        self, mock_generate
    ):
        self.payload["teams"][0]["goals"] = 10

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        mock_generate.assert_not_called()

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "mock-test-key"},
    )
    @patch("api.ai_summary.urlopen")
    def test_wrong_team_goals_returns_fallback(
        self, mock_urlopen
    ):
        mock_urlopen.return_value = self.provider_response(
            "Home scored 0 goals from 5 shots. "
            "Away scored 1 goal from 3 shots. "
            "Home recorded 0.80 xG and Away recorded 0.40 xG."
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assert_fallback(response)
        mock_urlopen.assert_called_once()

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "mock-test-key"},
    )
    @patch("api.ai_summary.urlopen")
    def test_wrong_team_shots_returns_fallback(
        self, mock_urlopen
    ):
        mock_urlopen.return_value = self.provider_response(
            "Home scored 1 goal from 3 shots. "
            "Away scored 0 goals from 5 shots. "
            "Home recorded 0.80 xG and Away recorded 0.40 xG."
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assert_fallback(response)
        mock_urlopen.assert_called_once()

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "mock-test-key"},
    )
    @patch("api.ai_summary.urlopen")
    def test_wrong_team_xg_returns_fallback(
        self, mock_urlopen
    ):
        mock_urlopen.return_value = self.provider_response(
            "Home scored 1 goal from 5 shots. "
            "Away scored 0 goals from 3 shots. "
            "Home recorded 0.40 xG and Away recorded 0.80 xG."
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assert_fallback(response)
        mock_urlopen.assert_called_once()
