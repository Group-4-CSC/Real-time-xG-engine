from Analytics.xg_model import compute_xg
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .ai_summary import SummaryInputSerializer, generate_summary
from rest_framework import status


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
def ai_match_summary(request):
    serializer = SummaryInputSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        summary = generate_summary(serializer.validated_data)
    except RuntimeError:
        return Response(
            {"error": "AI summary is temporarily unavailable."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    return Response({
        "summary": summary,
        "is_placeholder": False
    })

