import math
import unittest

from xg_geometry import (
    calculate_shot_angle,
    calculate_shot_distance,
    is_inside_penalty_box,
)


class XGGeometryTests(unittest.TestCase):
    def test_inside_and_outside_penalty_box(self):
        self.assertTrue(is_inside_penalty_box(90, 50))
        self.assertFalse(is_inside_penalty_box(80, 50))
        self.assertFalse(is_inside_penalty_box(90, 10))
        self.assertFalse(is_inside_penalty_box(90, 90))

    def test_exact_penalty_area_boundaries_are_inside(self):
        x_boundary = (105 - 16.5) / 105 * 100
        y_lower_boundary = (68 - 40.32) / 2 / 68 * 100
        y_upper_boundary = (68 + 40.32) / 2 / 68 * 100

        self.assertTrue(is_inside_penalty_box(x_boundary, 50))
        self.assertTrue(is_inside_penalty_box(100, y_lower_boundary))
        self.assertTrue(is_inside_penalty_box(100, y_upper_boundary))

    def test_distance_from_penalty_spot_is_eleven_meters(self):
        penalty_spot_x = 94 / 105 * 100

        self.assertAlmostEqual(
            calculate_shot_distance(penalty_spot_x, 50), 11.0, places=12
        )

    def test_shooting_angle_from_penalty_spot(self):
        penalty_spot_angle = math.degrees(2 * math.atan(3.66 / 11))

        self.assertAlmostEqual(
            calculate_shot_angle(94 / 105 * 100, 50),
            penalty_spot_angle,
            places=12,
        )
        self.assertAlmostEqual(penalty_spot_angle, 36.8, places=1)

    def test_distance_and_angle_are_symmetric_about_centerline(self):
        lower_side_y = 40
        upper_side_y = 60

        self.assertAlmostEqual(
            calculate_shot_distance(90, lower_side_y),
            calculate_shot_distance(90, upper_side_y),
            places=12,
        )
        self.assertAlmostEqual(
            calculate_shot_angle(90, lower_side_y),
            calculate_shot_angle(90, upper_side_y),
            places=12,
        )

    def test_geometry_is_calculated_outside_penalty_area(self):
        self.assertFalse(is_inside_penalty_box(50, 50))
        self.assertAlmostEqual(calculate_shot_distance(50, 50), 52.5, places=12)
        self.assertGreater(calculate_shot_angle(50, 50), 0)

    def test_rejects_invalid_coordinates(self):
        invalid_values = (
            "50",
            None,
            True,
            False,
            float("nan"),
            float("inf"),
            float("-inf"),
            -0.1,
            100.1,
        )
        functions = (
            is_inside_penalty_box,
            calculate_shot_distance,
            calculate_shot_angle,
        )

        for function in functions:
            for value in invalid_values:
                with self.subTest(function=function.__name__, x=value):
                    with self.assertRaises(ValueError):
                        function(value, 50)
                with self.subTest(function=function.__name__, y=value):
                    with self.assertRaises(ValueError):
                        function(50, value)

    def test_goal_line_center_has_zero_distance_and_180_degree_angle(self):
        self.assertEqual(calculate_shot_distance(100, 50), 0.0)
        self.assertAlmostEqual(calculate_shot_angle(100, 50), 180.0, places=12)

    def test_angle_is_undefined_at_either_goalpost(self):
        lower_post_y = (34 - 3.66) / 68 * 100
        upper_post_y = (34 + 3.66) / 68 * 100

        for post_y in (lower_post_y, upper_post_y):
            with self.subTest(post_y=post_y):
                self.assertIsNone(calculate_shot_angle(100, post_y))

    def test_angles_near_either_goalpost_are_finite(self):
        lower_post_y = (34 - 3.66) / 68 * 100
        upper_post_y = (34 + 3.66) / 68 * 100

        for post_y in (lower_post_y, upper_post_y):
            with self.subTest(post_y=post_y):
                angle = calculate_shot_angle(99.999999, post_y)
                self.assertIsInstance(angle, float)
                self.assertTrue(math.isfinite(angle))

    def test_distance_from_goalpost_is_half_goal_width(self):
        lower_post_y = (34 - 3.66) / 68 * 100
        upper_post_y = (34 + 3.66) / 68 * 100

        self.assertAlmostEqual(
            calculate_shot_distance(100, lower_post_y), 3.66, places=12
        )
        self.assertAlmostEqual(
            calculate_shot_distance(100, upper_post_y), 3.66, places=12
        )


if __name__ == "__main__":
    unittest.main()
