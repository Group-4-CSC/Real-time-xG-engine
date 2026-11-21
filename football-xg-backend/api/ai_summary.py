
"""AI match summary: only computed statistics enter the prompt."""

import json
import math
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

    def validate_name(self, value):
        if re.search(r"[\x00-\x1f\x7f]", value):
            raise serializers.ValidationError(
                "Team names cannot contain control characters."
            )

        return value

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

        if value["xg"] is not None and (
            not math.isfinite(value["xg"])
            or value["xg"] > value["xg_calculated_shots"]
        ):
            raise serializers.ValidationError(
                "xG must be finite and no larger than calculated shots."
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
    / "match_summary_v2.txt"
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


def _provider_input(stats):
    """Replace user-controlled identifiers with fixed, semantic-free slots."""
    return {
        "half": stats["half"],
        "teams": [
            {
                "name": f"team_{chr(ord('a') + index)}",
                "shots": team["shots"],
                "goals": team["goals"],
                "xg": team["xg"],
                "xg_calculated_shots": team["xg_calculated_shots"],
                "xg_missing_shots": team["xg_missing_shots"],
            }
            for index, team in enumerate(stats["teams"])
        ],
    }


def _expected_assessment(stats):
    first, second = stats["teams"]
    if first["goals"] == second["goals"]:
        score_winner = "draw"
    else:
        score_winner = (
            "team_a" if first["goals"] > second["goals"] else "team_b"
        )

    if first["xg"] is None or second["xg"] is None:
        xg_leader = "insufficient"
    elif math.isclose(
        first["xg"],
        second["xg"],
        rel_tol=0,
        abs_tol=0.01,
    ):
        xg_leader = "even"
    else:
        xg_leader = "team_a" if first["xg"] > second["xg"] else "team_b"

    coverage = (
        "partial"
        if any(team["xg_missing_shots"] > 0 for team in stats["teams"])
        else "complete"
    )
    return {
        "score_winner": score_winner,
        "xg_leader": xg_leader,
        "coverage": coverage,
    }


def _validate_provider_assessment(content, stats):
    try:
        assessment = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("AI assessment is not valid JSON.") from exc

    expected = _expected_assessment(stats)
    if assessment != expected:
        raise ValueError(
            "AI assessment does not match the validated match statistics."
        )

    return assessment


def _render_summary(stats, assessment):
    sentences = []
    names = {
        "team_a": stats["teams"][0]["name"],
        "team_b": stats["teams"][1]["name"],
    }

    for slot, team in zip(("team_a", "team_b"), stats["teams"]):
        name = names[slot]
        if team["xg"] is None:
            sentences.append(
                f"{name} scored {team['goals']} goals from "
                f"{team['shots']} shots; its xG is unknown with "
                f"{team['xg_calculated_shots']} supported shots."
            )
        else:
            sentences.append(
                f"{name} scored {team['goals']} goals from "
                f"{team['shots']} shots and recorded {team['xg']:.3f} "
                f"supported-shot xG from {team['xg_calculated_shots']} "
                f"of {team['shots']} shots."
            )

    if assessment["score_winner"] == "draw":
        sentences.append("The score was drawn.")
    else:
        sentences.append(
            f"The score winner was {names[assessment['score_winner']]}."
        )

    if assessment["xg_leader"] == "even":
        sentences.append("Supported-shot xG was even.")
    elif assessment["xg_leader"] == "insufficient":
        sentences.append(
            "The supported-shot xG comparison is unavailable."
        )
    else:
        sentences.append(
            f"{names[assessment['xg_leader']]} had higher "
            "supported-shot xG."
        )

    if assessment["coverage"] == "partial":
        sentences.append(
            "xG coverage is partial; totals do not represent every shot."
        )
    else:
        sentences.append("xG coverage is complete.")

    return " ".join(sentences)


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
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": load_system_prompt(),
            },
            {
                "role": "user",
                "content": json.dumps(
                    _provider_input(stats),
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
        content = data["choices"][0]["message"]["content"]
        assessment = _validate_provider_assessment(content, stats)
        return _render_summary(stats, assessment)

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
