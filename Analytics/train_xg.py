"""Experimental match-held-out logistic xG; never replaces the API heuristic."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from Analytics.xg_features import prepare_shot_features
from Analytics.xg_geometry import calculate_shot_angle, calculate_shot_distance, is_inside_penalty_box
from Analytics.xg_model import compute_xg

DEFAULT_CSV = Path(__file__).parent / "Data/Clean_Statsbomb_Data/shotCollection.csv"
OUTCOMES = {"goal", "saved", "blocked", "off_target", "post"}


def shot_features(shot):
    """Allowlist pre-shot inputs; labels and provider xG cannot enter X.

    Match the heuristic's support so both models can score identical shots.
    """
    normalized = prepare_shot_features(shot["x"], shot["y"], shot["body_part"])
    x, y = normalized["x_coord"], normalized["y_coord"]
    if not is_inside_penalty_box(x, y):
        return None
    angle = calculate_shot_angle(x, y)
    if angle is None:
        return None
    return [calculate_shot_distance(x, y), angle, normalized["body_part"]]


def load_shots(path):
    """Fail on invalid rows rather than silently turning unknown outcomes into misses."""
    shots = []
    seen = set()
    with Path(path).open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = {"id", "match_id", "x", "y", "body_part", "outcome"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing CSV columns: {sorted(missing)}")
        for line, row in enumerate(reader, 2):
            try:
                if not row["id"] or row["id"] in seen:
                    raise ValueError("empty or duplicate shot ID")
                match_id = row["match_id"]
                if not match_id or match_id != match_id.strip():
                    raise ValueError("match ID must be non-empty with no surrounding whitespace")
                if row["outcome"] not in OUTCOMES:
                    raise ValueError("unknown outcome")
                shot = {key: row[key] for key in required}
                shot.update(x=float(row["x"]), y=float(row["y"]))
                shot_features(shot)  # validate even excluded coordinates
                seen.add(shot["id"])
                shots.append(shot)
            except (TypeError, ValueError) as error:
                raise ValueError(f"CSV row {line}: {error}") from error
    if not shots:
        raise ValueError("CSV contains no shots")
    return shots


def build_model():
    """Fit scaling and categorical encoding on training shots only."""
    return Pipeline([
        ("features", ColumnTransformer([
            ("geometry", StandardScaler(), [0, 1]),
            ("body_part", OneHotEncoder(handle_unknown="ignore"), [2]),
        ])),
        ("classifier", LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000)),
    ])


def evaluate(labels, probabilities):
    return {
        "brier_score": float(brier_score_loss(labels, probabilities)),
        "log_loss": float(log_loss(labels, probabilities, labels=[0, 1])),
    }


def run_experiment(path=DEFAULT_CSV, seed=42, test_size=0.3):
    shots = load_shots(path)
    # Split ALL match IDs first, with a fixed seed; never choose a split by its score.
    groups = np.array([shot["match_id"] for shot in shots])
    if len(set(groups)) < 2:
        raise ValueError("At least two matches are required")
    train_all, test_all = next(GroupShuffleSplit(
        n_splits=1, test_size=test_size, random_state=seed
    ).split(shots, groups=groups))
    features = [shot_features(shot) for shot in shots]
    train = [int(i) for i in train_all if features[i] is not None]
    test = [int(i) for i in test_all if features[i] is not None]
    labels = np.array([int(shot["outcome"] == "goal") for shot in shots])
    if not train or not test or len(set(labels[train])) != 2:
        raise ValueError("Need supported shots in both splits and both labels in training")
    model = build_model()
    model.fit(np.array([features[i] for i in train], dtype=object), labels[train])
    probabilities = model.predict_proba(
        np.array([features[i] for i in test], dtype=object)
    )[:, 1]
    baseline = [compute_xg(shots[i]) for i in test]
    predictions = [
        {"shot_id": shots[i]["id"], "match_id": shots[i]["match_id"],
         "goal": int(labels[i]), "logistic_xg": float(probability),
         "heuristic_xg": float(heuristic)}
        for i, probability, heuristic in zip(test, probabilities, baseline)
    ]
    return {
        "dataset_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "sklearn_version": sklearn.__version__, "seed": seed, "test_size": test_size,
        "feature_names": ["distance_m", "angle_degrees", "body_part"],
        "total_shots": len(shots), "supported_shots": len(train) + len(test),
        "excluded_shots": len(shots) - len(train) - len(test),
        "train_match_ids": sorted(set(groups[train_all])),
        "test_match_ids": sorted(set(groups[test_all])),
        "train_shots": len(train), "test_shots": len(test),
        "train_goals": int(labels[train].sum()), "test_goals": int(labels[test].sum()),
        "logistic": evaluate(labels[test], probabilities),
        "heuristic": evaluate(labels[test], baseline),
        "predictions": predictions,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-size", type=float, default=0.3,
                        help="Fraction of matches held out for testing (default: 0.3)")
    parser.add_argument("--output", type=Path, help="Optional JSON report including paired test predictions")
    args = parser.parse_args()
    if args.output is not None:
        same_path = args.output.resolve() == args.csv.resolve()
        same_file = (args.output.exists() and args.csv.exists()
                     and args.output.samefile(args.csv))
        if same_path or same_file:
            parser.error("--output must be different from --csv; choose a separate JSON report path to avoid overwriting the dataset")
    result = run_experiment(args.csv, args.seed, args.test_size)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "predictions"}, indent=2))


if __name__ == "__main__":
    main()
