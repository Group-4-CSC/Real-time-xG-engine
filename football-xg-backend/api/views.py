from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .xg import compute_xg


class ShotXGInputSerializer(serializers.Serializer):
    x = serializers.FloatField(min_value=0, max_value=100)
    y = serializers.FloatField(min_value=0, max_value=100)
    body_part = serializers.ChoiceField(
        choices=("left_foot", "right_foot", "head", "other")
    )
    outcome = serializers.ChoiceField(
        choices=("goal", "saved", "blocked", "off_target", "post")
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

    return Response({"xg": round(compute_xg(serializer.validated_data), 4)})
