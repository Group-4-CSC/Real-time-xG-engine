"""Physical geometry helpers for shots recorded in normalized pitch coordinates."""

import math
from numbers import Real


PITCH_LENGTH_METERS = 105.0
PITCH_WIDTH_METERS = 68.0
PENALTY_AREA_DEPTH_METERS = 16.5
PENALTY_AREA_WIDTH_METERS = 40.32
GOAL_WIDTH_METERS = 7.32


def _validated_coordinates(x, y):
    coordinates = []
    for name, value in (("x", x), ("y", y)):
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError(f"{name} must be a finite number from 0 to 100")
        try:
            coordinate = float(value)
        except (OverflowError, TypeError, ValueError) as error:
            raise ValueError(
                f"{name} must be a finite number from 0 to 100"
            ) from error
        if not math.isfinite(coordinate) or not 0 <= coordinate <= 100:
            raise ValueError(f"{name} must be a finite number from 0 to 100")
        coordinates.append(coordinate)
    return coordinates


def _to_meters(x, y):
    return (
        x * PITCH_LENGTH_METERS / 100,
        y * PITCH_WIDTH_METERS / 100,
    )


def is_inside_penalty_box(x, y):
    """Return whether a valid normalized coordinate is in the attacking box.

    The penalty-area boundary is inclusive. This eligibility check is separate
    from the geometry functions, which calculate results anywhere on the pitch.
    """
    x, y = _validated_coordinates(x, y)
    x_meters, y_meters = _to_meters(x, y)
    box_start_x = PITCH_LENGTH_METERS - PENALTY_AREA_DEPTH_METERS
    box_start_y = (PITCH_WIDTH_METERS - PENALTY_AREA_WIDTH_METERS) / 2
    box_end_y = box_start_y + PENALTY_AREA_WIDTH_METERS
    return (
        x_meters >= box_start_x
        and box_start_y <= y_meters <= box_end_y
    )


def calculate_shot_distance(x, y):
    """Return distance in meters to the physical goal center.

    This calculation is defined for valid coordinates anywhere on the pitch,
    including coordinates outside the penalty area and on the goal line.
    """
    x, y = _validated_coordinates(x, y)
    x_meters, y_meters = _to_meters(x, y)
    goal_x = PITCH_LENGTH_METERS
    goal_y = PITCH_WIDTH_METERS / 2
    return math.hypot(goal_x - x_meters, goal_y - y_meters)


def calculate_shot_angle(x, y):
    """Return the angle between the physical goalposts in degrees.

    This calculation is defined for valid coordinates anywhere on the pitch,
    independently of penalty-area eligibility. At a goalpost, the vector to
    that post has zero length, so the angle is undefined and ValueError is
    raised.
    """
    x, y = _validated_coordinates(x, y)
    shot_x, shot_y = _to_meters(x, y)
    goal_x = PITCH_LENGTH_METERS
    goal_center_y = PITCH_WIDTH_METERS / 2
    half_goal_width = GOAL_WIDTH_METERS / 2

    lower_post = (goal_x, goal_center_y - half_goal_width)
    upper_post = (goal_x, goal_center_y + half_goal_width)
    lower_vector = (lower_post[0] - shot_x, lower_post[1] - shot_y)
    upper_vector = (upper_post[0] - shot_x, upper_post[1] - shot_y)

    if lower_vector == (0, 0) or upper_vector == (0, 0):
        raise ValueError("shot angle is undefined at a goalpost")

    cross_product = (
        lower_vector[0] * upper_vector[1]
        - lower_vector[1] * upper_vector[0]
    )
    dot_product = (
        lower_vector[0] * upper_vector[0]
        + lower_vector[1] * upper_vector[1]
    )
    return math.degrees(math.atan2(abs(cross_product), dot_product))
