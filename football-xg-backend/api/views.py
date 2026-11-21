import logging

from Analytics.xg_model import compute_xg
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .llm import MatchSummaryUnavailable, generate_match_summary


logger = logging.getLogger(__name__)


class ShotXGInputSerializer(serializers.Serializer):
    x = serializers.FloatField(min_value=0, max_value=100)
    y = serializers.FloatField(min_value=0, max_value=100)
    body_part = serializers.ChoiceField(
        choices=("left_foot", "right_foot", "head", "other")
    )
    outcome = serializers.ChoiceField(
        choices=("goal", "saved", "blocked", "off_target", "post")
    )
    statsbomb_xg = serializers.FloatField(
        required=False, allow_null=True, min_value=0, max_value=1
    )


class MatchSummaryInputSerializer(serializers.Serializer):
    home_score = serializers.IntegerField(min_value=0, max_value=50)
    away_score = serializers.IntegerField(min_value=0, max_value=50)
    home_shots = serializers.IntegerField(min_value=0, max_value=500)
    away_shots = serializers.IntegerField(min_value=0, max_value=500)
    home_xg = serializers.FloatField(min_value=0, max_value=100)
    away_xg = serializers.FloatField(min_value=0, max_value=100)


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok"})


@api_view(["POST"])
@permission_classes([AllowAny])
def calculate_xg(request):
    serializer = ShotXGInputSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    shot = {
        field: serializer.validated_data[field]
        for field in ("x", "y", "body_part", "outcome")
    }
    xg = compute_xg(shot)
    if xg is None:
        return Response({"xg": None, "xg_status": "unsupported"})

    return Response({"xg": round(xg, 4), "xg_status": "computed"})


@api_view(["POST"])
@permission_classes([AllowAny])
def match_summary(request):
    serializer = MatchSummaryInputSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    metrics = {
        field: serializer.validated_data[field]
        for field in (
            "home_score",
            "away_score",
            "home_shots",
            "away_shots",
            "home_xg",
            "away_xg",
        )
    }

    try:
        summary = generate_match_summary(metrics)
    except MatchSummaryUnavailable as exc:
        logger.warning("Match summary unavailable: %s", exc.reason)
        return Response({"summary": None, "summary_status": "unavailable"})

    return Response({"summary": summary, "summary_status": "generated"})
