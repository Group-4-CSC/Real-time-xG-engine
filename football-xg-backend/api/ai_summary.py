"""AI match summary: only computed statistics enter the prompt.

The provider is optional locally. Never send an API key to React.
"""
import json
import os
import re
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
            raise serializers.ValidationError("Goals cannot exceed shots.")
        if value["xg_calculated_shots"] + value["xg_missing_shots"] != value["shots"]:
            raise serializers.ValidationError("xG coverage must add up to shots.")
        if value["xg"] is None and value["xg_calculated_shots"] != 0:
            raise serializers.ValidationError("xG is required for calculated shots.")
        if value["xg"] is not None and value["xg_calculated_shots"] == 0:
            raise serializers.ValidationError("No calculated shots: xG must be null.")
        return value


class SummaryInputSerializer(serializers.Serializer):
    match_id = serializers.CharField(max_length=100)
    half = serializers.ChoiceField(choices=["all", "1", "2"])
    teams = TeamStatsSerializer(many=True)

    def validate_teams(self, value):
        if len(value) != 2 or value[0]["name"] == value[1]["name"]:
            raise serializers.ValidationError("Exactly two distinct teams are required.")
        return value


SYSTEM_PROMPT = (
    "You explain soccer match statistics to a casual fan. Write 3 to 5 short sentences. "
    "Use ONLY the provided JSON facts. Do not invent numbers, players, events, causes, "
    "or claims about match dominance. A missing xG is unknown, not zero. "
    "If any shots lack xG, explicitly state that xG is partial and cannot represent "
    "every chance. Avoid any numeric value not in the supplied JSON. "
    "Do not include markdown, bullet points, or additional commentary."
)


def _allowed_numbers(stats):
    # Permit the supplied values and common 2-decimal rendering of xG.
    allowed = set()
    for team in stats["teams"]:
        for key in ("shots", "goals", "xg_calculated_shots", "xg_missing_shots"):
            allowed.add(str(team[key]))
        if team["xg"] is not None:
            allowed.add(str(team["xg"]))
            allowed.add(f'{team["xg"]:.2f}')
    return allowed


def validate_summary(summary, stats):
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", summary.strip()) if s.strip()]
    if not 3 <= len(sentences) <= 5:
        raise ValueError("Summary must contain 3–5 sentences.")
    numbers = re.findall(r"(?<![\w])\d+(?:\.\d+)?(?![\w])", summary)
    if any(number not in _allowed_numbers(stats) for number in numbers):
        raise ValueError("Summary contains an unprovided number.")
    if any(t["xg_missing_shots"] > 0 for t in stats["teams"]):
        if not re.search(r"partial|incomplete|missing|not all", summary, re.I):
            raise ValueError("Summary must disclose incomplete xG.")
    return summary.strip()


def generate_summary(stats):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("AI summary is not configured on the server.")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(stats, separators=(",", ":"))},
        ],
    }
    request = Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            data = json.load(response)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError("AI service is unavailable.") from exc
    try:
        summary = data["choices"][0]["message"]["content"]
        return validate_summary(summary, stats)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError("AI response did not pass accuracy checks.") from exc
