"""Acceptance scenarios for the analytics owner's two capstone stories.

GEO-1: analyst receives physical distance/angle from normalized shot positions.
XG-1: analyst receives heuristic xG, or an explicit unsupported result.
The API contract is also exercised by football-xg-backend/api/tests.py.
"""
import math
import unittest

from Analytics.xg_features import prepare_shot_features
from Analytics.xg_geometry import calculate_shot_angle, calculate_shot_distance
from Analytics.xg_model import compute_xg


class GeometryStoryAcceptanceTests(unittest.TestCase):
    def test_given_penalty_spot_when_features_are_prepared_then_physical_geometry_is_correct(self):
        features = prepare_shot_features(94 / 105 * 100, 50, " Right Foot ")
        x, y = features["x_coord"], features["y_coord"]
        self.assertEqual(features["body_part"], "right_foot")
        self.assertAlmostEqual(calculate_shot_distance(x, y), 11.0, places=10)
        self.assertAlmostEqual(calculate_shot_angle(x, y), math.degrees(2 * math.atan(3.66 / 11)), places=10)

    def test_given_invalid_position_then_no_plausible_geometry_is_reported(self):
        for invalid in [-1, 101, float("nan"), True]:
            with self.subTest(x=invalid):
                for geometry in [calculate_shot_distance, calculate_shot_angle]:
                    with self.assertRaises(ValueError):
                        geometry(invalid, 50)


class XGStoryAcceptanceTests(unittest.TestCase):
    def test_given_supported_shot_then_probability_uses_features_not_result_or_provider_xg(self):
        shot = {"x": 90, "y": 50, "body_part": "right_foot"}
        probability = compute_xg(shot)
        self.assertTrue(math.isfinite(probability))
        self.assertGreater(probability, 0)
        self.assertLess(probability, 1)
        self.assertEqual(probability, compute_xg(dict(shot, outcome="goal", statsbomb_xg=0.99)))
        self.assertEqual(probability, compute_xg(dict(shot, outcome="saved", statsbomb_xg=0.01)))
        self.assertGreater(compute_xg(dict(shot, x=97)), probability)
        self.assertLess(compute_xg(dict(shot, body_part="head")), probability)

    def test_given_outside_box_or_goalpost_then_result_is_missing_not_zero(self):
        for x, y in [(80, 50), (100, (34 - 3.66) / 68 * 100)]:
            with self.subTest(x=x, y=y):
                self.assertIsNone(compute_xg({"x": x, "y": y, "body_part": "right_foot"}))

    def test_given_invalid_shot_then_reject_instead_of_inventing_xg(self):
        with self.assertRaises(ValueError):
            compute_xg({"x": 101, "y": 50, "body_part": "right_foot"})
