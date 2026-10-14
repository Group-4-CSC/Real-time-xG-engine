''' Basic preprocessing helpers for shot features.'''

RECOGNIZED_BODY_PARTS = {"left_foot", "right_foot", "head", "other"}

def prepare_shot_features(x_coord, y_coord, body_part):
	"""Validate and normalize the input features for a shot."""
	if isinstance(x_coord, bool) or not isinstance(x_coord, (int, float)):
		raise ValueError("x_coord must be numeric")
	if isinstance(y_coord, bool) or not isinstance(y_coord, (int, float)):
		raise ValueError("y_coord must be numeric")
	if not isinstance(body_part, str):
		raise ValueError("body_part must be a string")

	normalized_body_part = body_part.strip().lower().replace(" ", "_")
	if normalized_body_part not in RECOGNIZED_BODY_PARTS:
		normalized_body_part = "other"

	return {
		"x_coord": float(x_coord),
		"y_coord": float(y_coord),
		"body_part": normalized_body_part,
	}
