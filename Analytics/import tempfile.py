import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from Analytics.data_smoke_check import (
    CSV_REVISION,
    MATCH_CSV_REVISION,
    load_csv_texts,
)


class CSVLoadingTests(unittest.TestCase):

    def test_loads_local_csv_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "Analytics/Data/Clean_Statsbomb_Data"
            folder.mkdir(parents=True)

            (folder / "shotCollection.csv").write_text(
                "id,x,y\nS1,90,50\n", encoding="utf-8"
            )
            (folder / "matchCollection.csv").write_text(
                "MatchID\nM1\n", encoding="utf-8"
            )

            with patch("Analytics.data_smoke_check.subprocess.run") as run:
                shots, matches = load_csv_texts(root)

            self.assertIn("S1,90,50", shots)
            self.assertIn("M1", matches)
            run.assert_not_called()

    def test_uses_git_fallback_when_files_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch("Analytics.data_smoke_check.subprocess.run") as run:
                run.side_effect = [
                    Mock(stdout="remote shot data"),
                    Mock(stdout="remote match data"),
                ]

                shots, matches = load_csv_texts(Path(temp))

            self.assertEqual(shots, "remote shot data")
            self.assertEqual(matches, "remote match data")
            self.assertEqual(run.call_count, 2)
            self.assertEqual(
                run.call_args_list[0].args[0],
                ["git", "show", CSV_REVISION],
            )
            self.assertEqual(
                run.call_args_list[1].args[0],
                ["git", "show", MATCH_CSV_REVISION],
            )

    def test_does_not_mix_local_and_remote_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "Analytics/Data/Clean_Statsbomb_Data"
            folder.mkdir(parents=True)

            (folder / "shotCollection.csv").write_text(
                "outdated local shots", encoding="utf-8"
            )

            with patch("Analytics.data_smoke_check.subprocess.run") as run:
                run.side_effect = [
                    Mock(stdout="remote shots"),
                    Mock(stdout="remote matches"),
                ]

                shots, matches = load_csv_texts(root)

            self.assertEqual(shots, "remote shots")
            self.assertEqual(matches, "remote matches")


if __name__ == "__main__":
    unittest.main()