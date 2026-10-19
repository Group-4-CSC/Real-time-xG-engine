"""Smoke-check the xG heuristic against the committed StatsBomb shot CSV."""

import csv
import io
import math
import subprocess
from collections import defaultdict
from pathlib import Path

from Analytics.xg_geometry import calculate_shot_angle, is_inside_penalty_box
from Analytics.xg_model import compute_xg


CSV_REVISION = (
    "origin/JP-Soccer-Data-Insert:"
    "Analytics/Data/Clean_Statsbomb_Data/shotCollection.csv"
)
MATCH_CSV_REVISION = (
    "origin/JP-Soccer-Data-Insert:"
    "Analytics/Data/Clean_Statsbomb_Data/matchCollection.csv"
)


def load_csv_texts(repository_root):
    data_directory = repository_root / "Analytics" / "Data" / "Clean_Statsbomb_Data"
    shot_path = data_directory / "shotCollection.csv"
    match_path = data_directory / "matchCollection.csv"

    if shot_path.is_file() and match_path.is_file():
        try:
            return (
                shot_path.read_text(encoding="utf-8-sig"),
                match_path.read_text(encoding="utf-8-sig"),
            )
        except (OSError, UnicodeError):
            pass

    try:
        shot_result = subprocess.run(
            ["git", "show", CSV_REVISION],
            capture_output=True,
            text=True,
            encoding="utf-8-sig",
            check=True,
            cwd=repository_root,
        )
        match_result = subprocess.run(
            ["git", "show", MATCH_CSV_REVISION],
            capture_output=True,
            text=True,
            encoding="utf-8-sig",
            check=True,
            cwd=repository_root,
        )
    except (OSError, subprocess.CalledProcessError, UnicodeError) as error:
        raise SystemExit(
            "Unable to read both StatsBomb CSVs locally or from "
            "origin/JP-Soccer-Data-Insert. Place shotCollection.csv and "
            "matchCollection.csv in Analytics/Data/Clean_Statsbomb_Data/, "
            "or fetch the remote branch containing them."
        ) from error

    return shot_result.stdout, match_result.stdout


def main():
    repository_root = Path(__file__).resolve().parent.parent
    shot_text, match_text = load_csv_texts(repository_root)
    shot_reader = csv.DictReader(io.StringIO(shot_text))
    match_reader = csv.DictReader(io.StringIO(match_text))

    processed = 0
    successful = 0
    outside_model = 0
    undefined_angles = 0
    errors = 0
    predictions = []
    match_totals = defaultdict(float)
    required_shot_columns = {
        "id",
        "match_id",
        "team",
        "x",
        "y",
        "body_part",
    }
    required_match_columns = {"MatchID", "HomeTeamName", "AwayTeamName"}

    for label, reader, required_columns in (
        ("shot CSV", shot_reader, required_shot_columns),
        ("match CSV", match_reader, required_match_columns),
    ):
        missing_columns = sorted(
            required_columns.difference(reader.fieldnames or ())
        )
        for column in missing_columns:
            errors += 1
            print(f"Error: {label} is missing required column {column!r}")

    matches = {}
    if not required_match_columns.difference(match_reader.fieldnames or ()):
        for row_number, row in enumerate(match_reader, start=2):
            match_id = row["MatchID"]
            home_team = row["HomeTeamName"]
            away_team = row["AwayTeamName"]
            if not match_id or not home_team or not away_team:
                errors += 1
                print(
                    f"Error in match CSV row {row_number}: "
                    "MatchID, HomeTeamName, and AwayTeamName must be non-empty"
                )
                continue
            if match_id in matches:
                errors += 1
                print(
                    f"Error in match CSV row {row_number}: "
                    f"duplicate MatchID {match_id!r}"
                )
                continue
            matches[match_id] = {
                "home": home_team,
                "away": away_team,
                "teams": {
                    home_team: {
                        "shots": 0,
                        "supported": 0,
                        "outside": 0,
                        "xg": 0.0,
                    },
                    away_team: {
                        "shots": 0,
                        "supported": 0,
                        "outside": 0,
                        "xg": 0.0,
                    },
                },
            }

    shot_schema_valid = not required_shot_columns.difference(
        shot_reader.fieldnames or ()
    )
    match_schema_valid = not required_match_columns.difference(
        match_reader.fieldnames or ()
    )
    for row_number, row in enumerate(shot_reader, start=2):
        processed += 1
        shot_id = row.get("id", "")
        if not shot_schema_valid or not match_schema_valid:
            continue
        try:
            match_id = row["match_id"]
            team = row["team"]
            match = matches.get(match_id)
            if match is None:
                raise ValueError(f"unknown MatchID {match_id!r}")
            if team not in (match["home"], match["away"]):
                raise ValueError(
                    f"team {team!r} does not match either match team "
                    f"({match['home']!r}, {match['away']!r})"
                )

            team_stats = match["teams"][team]
            team_stats["shots"] += 1
            x = float(row["x"])
            y = float(row["y"])
            prediction = compute_xg(
                {
                    "x": x,
                    "y": y,
                    "body_part": row["body_part"],
                }
            )

            if prediction is None:
                if not is_inside_penalty_box(x, y):
                    outside_model += 1
                    team_stats["outside"] += 1
                elif calculate_shot_angle(x, y) is None:
                    undefined_angles += 1
                else:
                    raise ValueError(
                        "compute_xg returned None for an otherwise supported shot"
                    )
                continue

            if (
                isinstance(prediction, bool)
                or not isinstance(prediction, (int, float))
                or not math.isfinite(prediction)
                or not 0.0 <= prediction <= 1.0
            ):
                raise ValueError(
                    f"compute_xg returned an invalid numeric value: "
                    f"{prediction!r}"
                )

            successful += 1
            numeric_prediction = float(prediction)
            predictions.append(numeric_prediction)
            match_totals[match_id] += numeric_prediction
            team_stats["supported"] += 1
            team_stats["xg"] += numeric_prediction
        except Exception as error:
            errors += 1
            print(
                f"Error on row {row_number} (shot ID {shot_id!r}): "
                f"{type(error).__name__}: {error}"
            )

    for match_id, match in matches.items():
        team_xg_total = sum(
            stats["xg"] for stats in match["teams"].values()
        )
        match_xg_total = match_totals.get(match_id, 0.0)
        if not math.isclose(
            team_xg_total, match_xg_total, rel_tol=1e-12, abs_tol=1e-12
        ):
            errors += 1
            print(
                f"Error for MatchID {match_id!r}: team supported-shot xG "
                f"total {team_xg_total:.12f} does not match combined "
                f"match total {match_xg_total:.12f}"
            )

    print(f"Shots processed: {processed}")
    print(f"Successful numeric predictions: {successful}")
    print(f"Outside-model shots: {outside_model}")
    print(f"Undefined-angle shots: {undefined_angles}")
    print(f"Errors: {errors}")
    if predictions:
        print(f"Minimum numeric xG: {min(predictions):.6f}")
        print(f"Maximum numeric xG: {max(predictions):.6f}")
        print(f"Mean numeric xG: {sum(predictions) / len(predictions):.6f}")
    else:
        print("Minimum numeric xG: N/A")
        print("Maximum numeric xG: N/A")
        print("Mean numeric xG: N/A")

    print(
        "Total modeled xG per MatchID (supported shots only; "
        "excludes unsupported shots):"
    )
    for match_id in sorted(match_totals):
        print(f"  {match_id}: {match_totals[match_id]:.6f}")

    print(
        "Per-match team totals (supported-shot xG and xGD are partial, "
        "model-scope totals; unsupported shots are excluded):"
    )
    for match_id in sorted(matches):
        match = matches[match_id]
        home_team = match["home"]
        away_team = match["away"]
        home_stats = match["teams"][home_team]
        away_stats = match["teams"][away_team]
        home_xgd = home_stats["xg"] - away_stats["xg"]
        away_xgd = -home_xgd
        print(f"  Match ID: {match_id}")
        for team, stats, xgd in (
            (home_team, home_stats, home_xgd),
            (away_team, away_stats, away_xgd),
        ):
            print(
                f"    {team}: shots={stats['shots']}, "
                f"supported={stats['supported']}, "
                f"outside-model={stats['outside']}, "
                f"supported-shot xG={stats['xg']:.6f}, "
                f"supported-shot xGD={xgd:+.6f}"
            )

    print("These are heuristic predictions from an untrained, uncalibrated model.")

    if processed == 0 or errors > 0:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
