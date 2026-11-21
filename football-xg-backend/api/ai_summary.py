
"""AI match summary: only computed statistics enter the prompt."""

import json
import os
import re

from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from rest_framework import serializers


class TeamStatsSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    shots = serializers.IntegerField(min_value=0)
    goals = serializers.IntegerField(min_value=0)
    xg = serializers.FloatField(min_value=0, allow_null=True)
    xg_calculated_shots = serializers.IntegerField(min_value=0)
    xg_missing_shots = serializers.IntegerField(min_value=0)

    def validate(self, value):
        if value["goals"] > value["shots"]:
            raise serializers.ValidationError(
                "Goals cannot exceed shots."
            )

        if (
            value["xg_calculated_shots"]
            + value["xg_missing_shots"]
            != value["shots"]
        ):
            raise serializers.ValidationError(
                "xG coverage must add up to shots."
            )

        if (
            value["xg"] is None
            and value["xg_calculated_shots"] != 0
        ):
            raise serializers.ValidationError(
                "xG is required for calculated shots."
            )

        if (
            value["xg"] is not None
            and value["xg_calculated_shots"] == 0
        ):
            raise serializers.ValidationError(
                "No calculated shots: xG must be null."
            )

        return value


class SummaryInputSerializer(serializers.Serializer):
    match_id = serializers.CharField(max_length=100)
    half = serializers.ChoiceField(choices=["all", "1", "2"])
    teams = TeamStatsSerializer(many=True)

    def validate_teams(self, value):
        if len(value) != 2 or value[0]["name"] == value[1]["name"]:
            raise serializers.ValidationError(
                "Exactly two distinct teams are required."
            )

        return value


PROMPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "prompts"
    / "match_summary_v1.txt"
)


def load_system_prompt():
    try:
        prompt = PROMPT_PATH.read_text(encoding="utf-8")

        if not prompt.strip():
            raise RuntimeError(
                "AI prompt file is empty."
            )

        return prompt

    except (OSError, UnicodeError) as exc:
        raise RuntimeError(
            "AI prompt file is unavailable."
        ) from exc


def _allowed_numbers(stats):
    allowed = set()

    for team in stats["teams"]:
        for key in (
            "shots",
            "goals",
            "xg_calculated_shots",
            "xg_missing_shots",
        ):
            allowed.add(str(team[key]))

        if team["xg"] is not None:
            allowed.add(str(team["xg"]))
            allowed.add(f'{team["xg"]:.2f}')

    return allowed


def _validate_team_attribution(summary, stats):
    """Check explicit team-specific numerical claims.

    This is a limited validator, not a complete
    natural-language fact checker. Complex claims
    still require evaluator or human review.
    """

    for team in stats["teams"]:
        name = re.escape(team["name"])

        patterns = {
            "goals": [
                rf"(?<!\w){name}\s+(?:scored|recorded|had)\s+(\d+)\s+goals?\b",
            ],
            "shots": [
                rf"(?<!\w){name}\s+(?:recorded|had|attempted|took)\s+(\d+)\s+shots?\b",
                rf"(?<!\w){name}\s+scored\s+\d+\s+goals?\s+from\s+(\d+)\s+shots?\b",
            ],
            "xg": [
                rf"(?<!\w){name}\s+(?:recorded|had|generated)\s+(\d+(?:\.\d+)?)\s+xg\b",
            ],
        }

        for metric, metric_patterns in patterns.items():
            expected = team[metric]

            for pattern in metric_patterns:
                for match in re.finditer(
                    pattern,
                    summary,
                    re.I,
                ):
                    reported = float(match.group(1))

                    if expected is None:
                        raise ValueError(
                            "Summary reports an unavailable statistic."
                        )

                    allowed = {float(expected)}

                    if metric == "xg":
                        allowed.add(
                            float(f"{expected:.2f}")
                        )

                    if reported not in allowed:
                        raise ValueError(
                            f"Incorrect {metric} attributed to "
                            f"{team['name']}."
                        )


def validate_summary(summary, stats):
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError(
            "AI summary is empty or invalid."
        )

    sentences = [
        sentence.strip()
        for sentence in re.split(
            r"(?<=[.!?])\s+",
            summary.strip(),
        )
        if sentence.strip()
    ]

    if not 3 <= len(sentences) <= 5:
        raise ValueError(
            "Summary must contain 3–5 sentences."
        )

    numbers = re.findall(
        r"(?<![\w])\d+(?:\.\d+)?(?![\w])",
        summary,
    )

    if any(
        number not in _allowed_numbers(stats)
        for number in numbers
    ):
        raise ValueError(
            "Summary contains an unprovided number."
        )

    if any(
        team["xg_missing_shots"] > 0
        for team in stats["teams"]
    ):
        if not re.search(
            r"partial|incomplete|missing|not all",
            summary,
            re.I,
        ):
            raise ValueError(
                "Summary must disclose incomplete xG."
            )

    _validate_team_attribution(summary, stats)

    return summary.strip()


def generate_summary(stats):
    key = os.getenv("OPENAI_API_KEY")

    if not key:
        raise RuntimeError(
            "AI summary is not configured on the server."
        )

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": load_system_prompt(),
            },
            {
                "role": "user",
                "content": json.dumps(
                    stats,
                    separators=(",", ":"),
                ),
            },
        ],
    }

    request = Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=15) as response:
            data = json.load(response)

    except (
        HTTPError,
        URLError,
        TimeoutError,
        OSError,
        json.JSONDecodeError,
        UnicodeError,
    ) as exc:
        raise RuntimeError(
            "AI service is unavailable or returned invalid data."
        ) from exc

    try:
        summary = data["choices"][0]["message"]["content"]

        return validate_summary(summary, stats)

    except (
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        AttributeError,
    ) as exc:
        raise RuntimeError(
            "AI response did not pass accuracy checks."
        ) from exc


def generate_fallback_summary(stats):
    """Create a safe summary using only validated match statistics."""

    lines = []

    for team in stats["teams"]:
        name = team["name"]
        goals = team["goals"]
        shots = team["shots"]
        xg = team["xg"]
        missing = team["xg_missing_shots"]

        if xg is None:
            xg_text = "xG is unavailable"
        else:
            xg_text = f"xG is {xg:.2f}"

        if missing > 0:
            xg_text += " (incomplete xG data)"

        lines.append(
            f"{name}: {goals} goals, {shots} shots, {xg_text}."
        )

    return (
        "AI analysis is unavailable. "
        "Here are the recorded match statistics: "
        + " ".join(lines)
    )
