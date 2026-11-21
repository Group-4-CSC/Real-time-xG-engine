import json
import logging
import math
import re
from functools import lru_cache
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


logger = logging.getLogger(__name__)
PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "match_summary_v1.txt"
NUMBER_WORD_PATTERN = re.compile(
    r"\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"dozen|hundred|thousand|half|once|twice|thrice|double|triple)\b",
    re.IGNORECASE,
)
FACT_FIELDS = ("home_score", "away_score", "home_shots", "away_shots", "home_xg", "away_xg")


def _comparison(home, away, tolerance=0):
    if math.isclose(home, away, abs_tol=tolerance):
        return "level"
    return "home" if home > away else "away"


class MatchSummaryUnavailable(Exception):
    """Expected failure mode for an unavailable or unsafe summary."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


@lru_cache(maxsize=1)
def load_match_summary_prompt():
    try:
        return PROMPT_PATH.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise MatchSummaryUnavailable("prompt_unavailable") from exc


def _parse_provider_output(content, metrics):
    try:
        result = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        raise MatchSummaryUnavailable("invalid_output") from exc

    if not isinstance(result, dict) or set(result) != {
        "summary",
        "facts",
        "comparisons",
    }:
        raise MatchSummaryUnavailable("invalid_output")

    summary = result["summary"]
    facts = result["facts"]
    comparisons = result["comparisons"]
    if (
        not isinstance(summary, str)
        or not 30 <= len(summary.strip()) <= 350
        or re.search(r"\d", summary)
        or NUMBER_WORD_PATTERN.search(summary)
    ):
        raise MatchSummaryUnavailable("invalid_output")
    if not isinstance(facts, dict) or set(facts) != set(FACT_FIELDS):
        raise MatchSummaryUnavailable("invalid_output")

    for field in ("home_score", "away_score", "home_shots", "away_shots"):
        value = facts[field]
        if isinstance(value, bool) or not isinstance(value, int) or value != metrics[field]:
            raise MatchSummaryUnavailable("invalid_output")

    for field in ("home_xg", "away_xg"):
        value = facts[field]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isclose(value, metrics[field], abs_tol=0.0001)
        ):
            raise MatchSummaryUnavailable("invalid_output")

    expected_comparisons = {
        "score": _comparison(metrics["home_score"], metrics["away_score"]),
        "shots": _comparison(metrics["home_shots"], metrics["away_shots"]),
        "xg": _comparison(metrics["home_xg"], metrics["away_xg"], tolerance=0.005),
    }
    if comparisons != expected_comparisons:
        raise MatchSummaryUnavailable("invalid_output")

    return summary.strip()


def generate_match_summary(metrics):
    if not settings.OPENAI_API_KEY:
        raise MatchSummaryUnavailable("missing_api_key")

    prompt = load_match_summary_prompt()
    request_body = json.dumps(
        {
            "model": settings.OPENAI_MODEL,
            "temperature": 0.2,
            "max_tokens": 300,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": json.dumps(metrics, separators=(",", ":"), sort_keys=True),
                },
            ],
        }
    ).encode("utf-8")
    request = Request(
        settings.OPENAI_API_URL,
        data=request_body,
        headers={
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=settings.OPENAI_TIMEOUT_SECONDS) as response:
            provider_body = json.loads(response.read().decode("utf-8"))
    except (HTTPError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise MatchSummaryUnavailable("provider_error") from exc
    except (TimeoutError, URLError) as exc:
        reason = (
            "provider_timeout"
            if isinstance(exc, TimeoutError) or "timeout" in str(exc).lower()
            else "provider_unavailable"
        )
        raise MatchSummaryUnavailable(reason) from exc

    try:
        content = provider_body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise MatchSummaryUnavailable("provider_error") from exc

    if not isinstance(content, str):
        raise MatchSummaryUnavailable("provider_error")
    return _parse_provider_output(content, metrics)
