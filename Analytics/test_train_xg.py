"""Regression checks for leakage, shared support, and held-out evaluation."""
import csv
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from sklearn.metrics import brier_score_loss, log_loss

from Analytics.train_xg import DEFAULT_CSV, build_model, load_shots, main, run_experiment, shot_features
from Analytics.xg_geometry import calculate_shot_angle, calculate_shot_distance
from Analytics.xg_model import compute_xg


class TrainingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_experiment()

    def test_features_reuse_geometry_and_ignore_outcome_and_provider_xg(self):
        shot = dict(x=90, y=50, body_part="Right Foot")
        expected = [calculate_shot_distance(90, 50), calculate_shot_angle(90, 50), "right_foot"]
        self.assertEqual(shot_features(shot), expected)
        for outcome in ["goal", "saved"]:
            self.assertEqual(shot_features(dict(shot, outcome=outcome, statsbomb_xg=0.99, xg=1)), expected)

    def test_support_matches_heuristic_for_entire_dataset(self):
        for shot in load_shots(DEFAULT_CSV):
            self.assertEqual(shot_features(shot) is None, compute_xg(shot) is None)
        self.assertIsNone(shot_features(dict(x=100, y=(34-3.66)/68*100, body_part="head")))
        with self.assertRaises(ValueError):
            shot_features(dict(x=float("nan"), y=50, body_part="head"))

    def test_matches_do_not_cross_split_and_all_matches_are_accounted_for(self):
        result = self.result
        train, test = set(result['train_match_ids']), set(result['test_match_ids'])
        self.assertFalse(train & test)
        self.assertEqual(train | test, {s['match_id'] for s in load_shots(DEFAULT_CSV)})
        self.assertTrue(all(p['match_id'] in test for p in result['predictions']))
        self.assertEqual(result['supported_shots'] + result['excluded_shots'], result['total_shots'])

    def test_paired_predictions_labels_and_metrics_are_correct(self):
        result = self.result
        shots = {s['id']: s for s in load_shots(DEFAULT_CSV)}
        predictions = result['predictions']
        self.assertEqual(len(predictions), result['test_shots'])
        self.assertEqual(len({p['shot_id'] for p in predictions}), len(predictions))
        expected_ids = {s['id'] for s in shots.values() if s['match_id'] in result['test_match_ids'] and shot_features(s) is not None}
        self.assertEqual({p['shot_id'] for p in predictions}, expected_ids)
        for p in predictions:
            self.assertEqual(p['goal'], int(shots[p['shot_id']]['outcome'] == 'goal'))
            self.assertEqual(p['heuristic_xg'], compute_xg(shots[p['shot_id']]))
            self.assertTrue(np.isfinite(p['logistic_xg']))
            self.assertTrue(0 <= p['logistic_xg'] <= 1)
        y = [p['goal'] for p in predictions]
        for name in ['logistic', 'heuristic']:
            probabilities = [p[name + '_xg'] for p in predictions]
            self.assertAlmostEqual(result[name]['brier_score'], brier_score_loss(y, probabilities))
            self.assertAlmostEqual(result[name]['log_loss'], log_loss(y, probabilities, labels=[0, 1]))

    def test_preprocessing_fits_only_training_values_and_handles_unseen_body_part(self):
        model = build_model()
        x = np.array([[10, 20, 'head'], [20, 40, 'head'], [30, 60, 'head'], [40, 80, 'head']], dtype=object)
        model.fit(x, [0, 1, 0, 1])
        scaler = model.named_steps['features'].named_transformers_['geometry']
        np.testing.assert_allclose(scaler.mean_, [25, 50])
        p = model.predict_proba(np.array([[100, 170, 'other']], dtype=object))
        self.assertTrue(np.isfinite(p).all())
        np.testing.assert_allclose(scaler.mean_, [25, 50])

    def test_same_seed_is_reproducible(self):
        self.assertEqual(self.result, run_experiment())

    def test_bad_dataset_fails_with_context(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'shots.csv'
            path.write_text('x,y\n90,50\n')
            with self.assertRaisesRegex(ValueError, 'Missing CSV columns'):
                load_shots(path)
            fields = ['id', 'match_id', 'x', 'y', 'body_part', 'outcome']
            valid = dict(id='one', match_id='match', x=90, y=50, body_part='head', outcome='goal')
            for rows, message in [([dict(valid, outcome='unknown')], 'row 2'), ([valid, valid], 'duplicate'), ([dict(valid, match_id='')], 'match ID')]:
                with path.open('w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(rows)
                with self.assertRaisesRegex(ValueError, message):
                    load_shots(path)
            with path.open('w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerow(valid)
            with self.assertRaisesRegex(ValueError, 'two matches'):
                run_experiment(path)


class InputSafetyTests(unittest.TestCase):
    def assert_output_rejected(self, csv_path, output_path):
        original = csv_path.read_bytes()
        argv = ["train_xg", "--csv", str(csv_path), "--output", str(output_path)]
        with patch("sys.argv", argv), patch("sys.stderr", new_callable=io.StringIO) as stderr, \
                patch("Analytics.train_xg.run_experiment") as experiment, \
                patch.object(Path, "mkdir") as mkdir, patch.object(Path, "write_text") as write:
            with self.assertRaises(SystemExit) as error:
                main()
            self.assertEqual(error.exception.code, 2)
            self.assertIn("avoid overwriting the dataset", stderr.getvalue())
            experiment.assert_not_called()
            mkdir.assert_not_called()
            write.assert_not_called()
        self.assertEqual(csv_path.read_bytes(), original)

    def test_identical_output_path_is_rejected_before_experiment_or_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shots.csv"
            path.write_text("original dataset")
            self.assert_output_rejected(path, path)

    def test_equivalent_relative_and_absolute_paths_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            absolute = Path(directory).resolve() / "shots.csv"
            absolute.write_text("original dataset")
            relative = absolute.relative_to(Path.cwd())
            self.assert_output_rejected(relative, absolute)
            self.assert_output_rejected(absolute, relative.parent / ".." / relative.parent.name / relative.name)

    def test_symlink_output_alias_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shots.csv"
            path.write_text("original dataset")
            alias = path.with_name("alias.json")
            try:
                alias.symlink_to(path)
            except (OSError, NotImplementedError):
                self.skipTest("Symbolic links are unavailable on this platform")
            self.assert_output_rejected(path, alias)

    def test_hardlink_output_alias_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shots.csv"
            path.write_text("original dataset")
            alias = path.with_name("alias.json")
            try:
                os.link(path, alias)
            except (OSError, NotImplementedError):
                self.skipTest("Hard links are unavailable on this platform")
            self.assert_output_rejected(path, alias)

    def test_distinct_output_path_writes_report_without_changing_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shots.csv"
            path.write_text("original dataset")
            output = path.parent / "reports" / "result.json"
            with patch("sys.argv", ["train_xg", "--csv", str(path), "--output", str(output)]), \
                    patch("Analytics.train_xg.run_experiment", return_value={"predictions": []}), \
                    patch("sys.stdout", new_callable=io.StringIO):
                main()
            self.assertEqual(json.loads(output.read_text()), {"predictions": []})
            self.assertEqual(path.read_text(), "original dataset")

    def test_invalid_match_ids_never_reach_split(self):
        # Include a valid row first: validation must finish before splitting anything.
        header = "id,x,y,body_part,outcome,match_id\n"
        valid = "good,90,50,head,goal,18235\n"
        for invalid in [None, "", " ", "\t", " 18235", "18235 ", "\t18235", "18235\t"]:
            with self.subTest(match_id=invalid):
                row = "bad,90,50,head,saved" + ("" if invalid is None else "," + invalid) + "\n"
                with patch.object(Path, "open", return_value=io.StringIO(header + valid + row)), \
                        patch("Analytics.train_xg.GroupShuffleSplit") as splitter:
                    with self.assertRaisesRegex(ValueError, "CSV row 3: match ID"):
                        run_experiment(Path("in-memory.csv"))
                    splitter.assert_not_called()
        with patch.object(Path, "open", return_value=io.StringIO("id,x,y,body_part,outcome\n")), \
                patch("Analytics.train_xg.GroupShuffleSplit") as splitter:
            with self.assertRaisesRegex(ValueError, "Missing CSV columns.*match_id"):
                run_experiment(Path("in-memory.csv"))
            splitter.assert_not_called()

    def test_valid_match_ids_are_preserved(self):
        text = "id,x,y,body_part,outcome,match_id\na,90,50,head,goal,0018235\nb,90,50,head,saved,final-2\n"
        with patch.object(Path, "open", return_value=io.StringIO(text)):
            self.assertEqual([s["match_id"] for s in load_shots(Path("in-memory.csv"))],
                             ["0018235", "final-2"])


if __name__ == '__main__':
    unittest.main()
