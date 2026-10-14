import math

from Analytics.xg_geometry import calculate_shot_angle, is_inside_penalty_box

try:
    from Analytics.xg_model import compute_xg as analytics_compute_xg
except ModuleNotFoundError as error:
    if error.name != "Analytics.xg_model":
        raise
    analytics_compute_xg = None


def compute_xg(shot):
    """Use the analytics model when installed, otherwise a temporary fallback."""
    x = shot["x"]
    y = shot["y"]
    body_part = shot["body_part"]

    if not is_inside_penalty_box(x, y) or calculate_shot_angle(x, y) is None:
        return None

    if analytics_compute_xg is not None:
        return analytics_compute_xg(shot)

    centrality = 1 - abs(y - 50) / 50
    logit = -4.0 + (0.035 * x) + (0.75 * centrality)
    if body_part == "head":
        logit -= 0.5
    elif body_part == "other":
        logit -= 0.25

    return 1 / (1 + math.exp(-logit))