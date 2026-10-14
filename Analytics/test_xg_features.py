import unittest

from xg_features import prepare_shot_features


class PrepareShotFeaturesTests(unittest.TestCase):
    def test_accepts_valid_numeric_coordinates(self):
        result = prepare_shot_features(12.5, 8.25, "left_foot")

        self.assertEqual(result["x_coord"], 12.5)
        self.assertEqual(result["y_coord"], 8.25)

    def test_converts_integer_coordinates_to_floats(self):
        result = prepare_shot_features(12, 8, "left_foot")

        self.assertIs(type(result["x_coord"]), float)
        self.assertIs(type(result["y_coord"]), float)

    def test_normalizes_right_foot(self):
        result = prepare_shot_features(12, 8, "Right Foot")

        self.assertEqual(result["body_part"], "right_foot")

    def test_strips_and_normalizes_head(self):
        result = prepare_shot_features(12, 8, "  HEAD  ")

        self.assertEqual(result["body_part"], "head")

    def test_maps_unknown_body_part_to_other(self):
        result = prepare_shot_features(12, 8, "chest")

        self.assertEqual(result["body_part"], "other")

    def test_rejects_non_numeric_x_coordinate(self):
        with self.assertRaises(ValueError):
            prepare_shot_features("near", 8, "left_foot")

    def test_rejects_non_numeric_y_coordinate(self):
        with self.assertRaises(ValueError):
            prepare_shot_features(12, "far", "left_foot")

    def test_rejects_non_string_body_part(self):
        with self.assertRaises(ValueError):
            prepare_shot_features(12, 8, None)

    def test_rejects_boolean_coordinates(self):
        for coordinate in (True, False):
            with self.subTest(coordinate=coordinate):
                with self.assertRaises(ValueError):
                    prepare_shot_features(coordinate, 8, "left_foot")

                with self.assertRaises(ValueError):
                    prepare_shot_features(12, coordinate, "left_foot")


if __name__ == "__main__":
    unittest.main()
