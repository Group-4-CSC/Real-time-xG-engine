"""Transparent baseline xG heuristic for supported penalty-area shots.

This is a temporary, untrained heuristic. Its logistic score uses physical
shot distance, visible goal angle, and body part:
``sigmoid(intercept + distance_coefficient * distance
+ angle_coefficient * angle + body_part_modifier)``.
It is not trained or calibrated.
"""

import math

from Analytics.xg_features import prepare_shot_features
from Analytics.xg_geometry import (
    calculate_shot_angle,
    calculate_shot_distance,
    is_inside_penalty_box,
)


LOGIT_INTERCEPT = -1.5
DISTANCE_COEFFICIENT = -0.12
ANGLE_COEFFICIENT = 0.025
BODY_PART_MODIFIERS = {
    "left_foot": 0.0,
    "right_foot": 0.0,
    "head": -0.7,
    "other": -0.25,
}


def compute_xg(shot):
    """Return heuristic xG in [0, 1], or None for unsupported/undefined shots.

    ``shot`` must provide ``x``, ``y``, and ``body_part``. Other fields,
    including outcome and any existing xG value, do not affect the estimate.
    Valid shots outside the attacking penalty area and shots exactly at a
    goalpost return ``None``.
    """
    if not isinstance(shot, dict):
        raise ValueError("shot must be a dictionary")
    missing_fields = {"x", "y", "body_part"}.difference(shot)
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"shot is missing required fields: {missing}")

    features = prepare_shot_features(
        shot["x"],
        shot["y"],
        shot["body_part"],
    )
    x = features["x_coord"]
    y = features["y_coord"]
    body_part = features["body_part"]

    if not is_inside_penalty_box(x, y):
        return None

    distance = calculate_shot_distance(x, y)
    angle = calculate_shot_angle(x, y)
    if angle is None:
        return None

    logit = (
        LOGIT_INTERCEPT
        + DISTANCE_COEFFICIENT * distance
        + ANGLE_COEFFICIENT * angle
        + BODY_PART_MODIFIERS[body_part]
    )
    return 1.0 / (1.0 + math.exp(-logit))
