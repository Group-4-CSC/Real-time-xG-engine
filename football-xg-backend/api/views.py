import math

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok"})


@api_view(["POST"])
@permission_classes([AllowAny])
def calculate_xg(request):
    """Temporary placeholder; replace with the team's analytics module."""
    distance = float(request.data.get("distance_to_goal_m", 0.0) or 0.0)
    angle = float(request.data.get("angle_to_goal_deg", 0.0) or 0.0)
    is_header = bool(request.data.get("is_header", False))
    is_penalty = bool(request.data.get("is_penalty", False))

    if distance < 0:
        distance = 0.0
    if angle < 0:
        angle = 0.0
    if angle > 90:
        angle = 90.0

    logit = -2.8 - (0.06 * distance) + (0.02 * angle)
    if is_header:
        logit -= 0.6
    if is_penalty:
        logit += 2.0

    xg = 1 / (1 + math.exp(-logit))

    return Response(
        {
            "xg": round(xg, 4),
            "distance_to_goal_m": round(distance, 2),
            "angle_to_goal_deg": round(angle, 2),
            "is_header": is_header,
            "is_penalty": is_penalty,
        }
    )
