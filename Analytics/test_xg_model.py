import math
import unittest

from Analytics.xg_model import compute_xg


class XGModelTests(unittest.TestCase):
    def test_normal_in_box_shot_returns_probability(self):
        xg = compute_xg({"x": 90, "y": 50, "body_part": "right_foot"})

        self.assertIsInstance(xg, float)
        self.assertTrue(math.isfinite(xg))
        self.assertGreaterEqual(xg, 0.0)
        self.assertLessEqual(xg, 1.0)

    def test_closer_centered_shot_has_higher_xg(self):
        close_shot = {"x": 98, "y": 50, "body_part": "right_foot"}
        far_shot = {"x": 85, "y": 50, "body_part": "right_foot"}

        self.assertGreater(compute_xg(close_shot), compute_xg(far_shot))

    def test_symmetric_shot_positions_have_equivalent_xg(self):
        lower_shot = {"x": 90, "y": 40, "body_part": "left_foot"}
        upper_shot = {"x": 90, "y": 60, "body_part": "left_foot"}

        self.assertAlmostEqual(
            compute_xg(lower_shot), compute_xg(upper_shot), places=14
        )

    def test_headed_shot_has_lower_xg_than_foot_shot(self):
        foot_shot = {"x": 90, "y": 50, "body_part": "right_foot"}
        headed_shot = {"x": 90, "y": 50, "body_part": "head"}

        self.assertLess(compute_xg(headed_shot), compute_xg(foot_shot))

    def test_outcome_does_not_change_estimate(self):
        shot = {"x": 90, "y": 50, "body_part": "right_foot"}
        goal_shot = dict(shot, outcome="goal")
        saved_shot = dict(shot, outcome="saved")

        self.assertEqual(compute_xg(goal_shot), compute_xg(saved_shot))

    def test_outside_box_shot_returns_none_not_zero(self):
        self.assertIsNone(
            compute_xg({"x": 80, "y": 50, "body_part": "right_foot"})
        )

    def test_exact_goalpost_shot_returns_none(self):
        lower_post_y = (34 - 3.66) / 68 * 100

        self.assertIsNone(
            compute_xg(
                {"x": 100, "y": lower_post_y, "body_part": "right_foot"}
            )
        )

    def test_invalid_or_missing_inputs_raise_value_error(self):
        invalid_shots = (
            None,
            {"y": 50, "body_part": "right_foot"},
            {"x": 90, "body_part": "right_foot"},
            {"x": 90, "y": 50},
            {"x": "90", "y": 50, "body_part": "right_foot"},
            {"x": 90, "y": 101, "body_part": "right_foot"},
            {"x": 90, "y": 50, "body_part": None},
        )

        for shot in invalid_shots:
            with self.subTest(shot=shot):
                with self.assertRaises(ValueError):
                    compute_xg(shot)

    def test_same_shot_always_gives_same_result(self):
        shot = {"x": 92.5, "y": 48.0, "body_part": "head"}

        self.assertEqual(compute_xg(shot), compute_xg(shot))


if __name__ == "__main__":
    unittest.main()
