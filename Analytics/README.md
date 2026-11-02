# xG Insights: Python Analytics / Machine Learning

This package contains reusable shot preprocessing and geometry, the existing
untrained xG heuristic, and a separate experimental logistic-regression pipeline.
The experiment does **not** change `compute_xg()`, the Django API, frontend, or database.
It runs offline on the committed cleaned StatsBomb CSV and requires no credentials.

## Run the Friday milestone experiment

From the repository root, using Python 3.12 or newer.

Linux/macOS (Bash):

```bash
python -m venv Analytics/.venv
source Analytics/.venv/bin/activate
python -m pip install -r Analytics/requirements-ml.txt
python -m Analytics.train_xg --output Analytics/.venv/xg-experiment.json
python -m unittest discover -s Analytics -p 'test_*.py'
```

Windows PowerShell:

```powershell
py -3.12 -m venv Analytics/.venv
.\Analytics\.venv\Scripts\python.exe -m pip install -r Analytics/requirements-ml.txt
.\Analytics\.venv\Scripts\python.exe -m Analytics.train_xg --output Analytics/.venv/xg-experiment.json
.\Analytics\.venv\Scripts\python.exe -m unittest discover -s Analytics -p 'test_*.py'
.\Analytics\.venv\Scripts\python.exe -m Analytics.data_smoke_check
```

The PowerShell commands call the virtual environment's Python directly, so no
activation or execution-policy change is needed. `Analytics/.venv` is ignored by
Git and keeps the environment and generated report out of the review diff.
The Bash equivalent of the smoke check is `python -m Analytics.data_smoke_check`.
Windows commands are provided for portability; validation here ran on Linux.

The ML requirements are separate so existing heuristic/API users do not need
scikit-learn. The experiment uses the standard library to read CSVs; pandas is
only needed for the separate data-cleaning script. During this run, Python
3.12.14, NumPy 2.5.4, SciPy 1.18.1, and scikit-learn 1.9.1 were used.

The default input is `Analytics/Data/Clean_Statsbomb_Data/shotCollection.csv`.
Optional CLI arguments: `--csv PATH`, `--seed INTEGER` (default 42),
`--test-size FRACTION` (default 0.3), and `--output PATH`. The output directory
is created if needed; an existing output file at the specified path is replaced.
The output must not refer to the input CSV: identical paths, equivalent relative
and absolute paths, symbolic links, and hard links to the input are rejected
before training or writing anything.
The command prints the counts, held-out match IDs, and metrics. The optional JSON
also records every held-out shot ID, actual label, and both predictions, plus the
dataset SHA-256 and scikit-learn version. It stores a report, not a deployed or
serialized prediction model. Re-running the command retrains the model.

The actual milestone run is saved in
[`experiments/logistic_seed42.json`](experiments/logistic_seed42.json).
The default seed was used once, without searching for a favorable split or tuning
hyperparameters against the test set. Changing the seed is a new experiment;
do not choose a seed because it produces a better test score.

## How the model works

Logistic regression learns weights that turn a shot's features into a probability
between zero and one. Here its inputs are only:

- Distance to the goal center in meters, from `calculate_shot_distance()`.
- Visible goal angle in degrees, from `calculate_shot_angle()`.
- Normalized body part from `prepare_shot_features()`, encoded as category indicators.

These reuse the existing 105 × 68 meter reference pitch, 7.32 meter goal, and
normalized 0–100 coordinates attacking toward x = 100. The pipeline scales the
two numeric inputs and one-hot encodes body part. Both transformations are fitted
on training shots only. Unseen body-part categories are handled without failing.
The classifier uses L2 regularization with C = 1, lbfgs, and max_iter = 1000;
there is no class reweighting or hyperparameter search.

The training answer (label) is 1 for `outcome == "goal"`, otherwise 0 for the
known non-goal outcomes saved, blocked, off_target, and post. Unknown outcomes
fail validation rather than being silently counted as misses. **Outcome is never
an input feature.** Neither `statsbomb_xg` nor the existing `xg`, shot end
location, player, team, match ID, or any other CSV field enters the model.
Match ID is used only to keep training and test games separate. The feature
function can predict from x, y, and body part without knowing the outcome.

`GroupShuffleSplit` assigns whole matches to training or testing with seed 42
before filtering for model support. `test_size=0.3` holds out 30% of the
unique matches (rounded up: five of fourteen here), not 30% of individual shots.
The resulting supported-shot counts are 169 training and 78 testing.
No match appears in both sets. The model
never fits on test shots or test labels. It is then compared with the untouched
heuristic using exactly the same test-shot IDs and actual labels.

## Actual results

The CSV contains 429 shots from 14 Champions League finals and 47 goals.
The cleaning script excludes period-5 penalty shootouts; periods 1–4 remain,
including six in-match penalties in the full dataset.

Both models are evaluated only on the heuristic's supported scope: shots inside
the attacking penalty box with a defined goal angle. There are 247 supported
shots and 182 excluded shots, all outside the box in this dataset. Excluded shots
are never assigned zero xG and are absent from both models' metrics.

| Split | Matches | Supported shots | Actual goals |
| --- | ---: | ---: | ---: |
| Training | 9 | 169 | 28 |
| Testing | 5 | 78 | 13 |

Test match IDs: `18235`, `18242`, `22912`, `3750200`, `3750201`.
All train IDs and paired predictions are recorded in the JSON report.

| Model | Brier score ↓ | Log loss ↓ |
| --- | ---: | ---: |
| Experimental logistic regression | 0.129429 | 0.411071 |
| Existing heuristic | 0.126162 | 0.405393 |

Lower is better for both metrics. Brier score averages the squared difference
between each predicted probability and the actual 0/1 result. Log loss penalizes
confident wrong predictions particularly strongly. Logistic regression was
slightly worse on this held-out sample: +0.003267 Brier and +0.005678 log loss.
Training a model does not automatically make it better than a hand-written rule.
These results support keeping the experiment separate from the application.

## Tests and validation

`python -m unittest discover -s Analytics -p 'test_*.py'` ran **46 tests, all passing**:
32 existing tests plus 14 experiment tests (7 pipeline tests and 7 input-safety
tests). New checks cover reuse of
geometry, outcome/provider-xG exclusion, parity with heuristic support, disjoint
match splits, complete paired test coverage, actual-goal labels, metric
recomputation, training-only preprocessing, unseen categories, deterministic
reruns, and clear failure on malformed data. Existing tests still check that
unsupported heuristic shots return `None`, not zero.

The CSV loader rejects missing required columns, empty or duplicate shot IDs,
missing, empty, whitespace-only, or whitespace-padded match IDs, unknown
outcomes, and invalid/nonfinite coordinates with row
context. An experiment also rejects an empty CSV, fewer than two matches,
empty supported splits, or training labels containing only one class. Input-safety
tests prove invalid match IDs are rejected before the splitter is constructed,
valid IDs are preserved, output aliases cannot overwrite the input, and a separate
report path still works. Link tests may be skipped on platforms without link
support; none were skipped in the Linux validation run.

## Limitations and next steps

This is a small learning experiment, not a validated production model. Only 14
finals are available and only five are in this test set. Match grouping prevents
same-match leakage but does not make players, teams, or seasons independent.
Finals are a selective sample; performance may not transfer to league matches.
This random split is not a future-season forecast, and one split provides no
uncertainty estimate. No statistical superiority or calibration claim is made.

The model covers penalty-area shots only and omits useful context such as
pressure, goalkeeper position, assist type, and shot type. In-match penalties
are mixed with other shots without a penalty indicator. Body-part categories
are sparse (only two `other` shots in the full dataset). Geometry assumes one
reference pitch size. These choices limit what its probabilities can represent.

A later milestone can add more representative matches, use grouped validation
inside the training set for model selection, inspect calibration, and evaluate
once on a fresh untouched test set. Changing features after reviewing these
results would make this test set development evidence, not an untouched final
benchmark. Model persistence, inference integration, database writes, and model
replacement are outside this milestone.

## Existing modules and data credit

- `xg_features.py`: input/body-part normalization.
- `xg_geometry.py`: coordinate validation, penalty-box support, distance, and angle.
- `xg_model.py`: transparent, untrained heuristic; unchanged by this experiment.
- `data_smoke_check.py`: existing dataset/heuristic checks, runnable with
  `python -m Analytics.data_smoke_check` from the repository root.
- `Data/Data_Cleaning.py`: separate offline conversion of StatsBomb JSON to CSV;
  see `Data/README.md`. The experiment reads the committed CSV without rewriting it.

Data credit: [StatsBomb Open Data](https://github.com/hudl/open-data).

## Team responsibilities and planned integration

The existing division of work remains: Alejandro owns analytics and xG logic,
Joseph owns the Django/DRF backend, and Jason owns MongoDB structure and database
work. Analytics supports shot validation, feature engineering, model evaluation,
and eventual match-level team xG and xGD calculations.

The existing user stories remain project goals:

- Given valid supported penalty-area shots, calculate numeric xG between zero
  and one and eventually save predictions to the database. Unsupported shots
  must remain missing (`None`), never fabricated zeros. This offline experiment
  implements training/evaluation only; it does not implement database persistence.
- Given stored match shots, show total team xG and xG differential in the match
  summary. Any totals that exclude unsupported shots must state that they cover
  supported shots only.

The current API already calls the heuristic through
`POST /api/xg/calculate/`. Replacing it with a trained model, agreeing database
schemas and persistence, and wiring trained predictions into match summaries
require separate team decisions and implementation. The intended integration
remains Django/DRF → analytics model → API response and database storage.

## AI assistance and personal verification

Earlier project documentation records GitHub Copilot assistance with feature
preprocessing and tests, and ChatGPT assistance with planning, explanations,
review, and Git workflow. Codex assisted with this experimental training pipeline,
regression tests, evaluation, documentation, and review fixes. Codex ran the
reported checks; this does not claim the student has personally verified them.

Before submission, the analytics owner should read and explain the feature/label
separation, match split, metrics, and limitations; rerun the experiment and tests
locally; check the PowerShell commands on Windows if applicable; and confirm
that the work and AI disclosure meet the course requirements. Team decisions
and final acceptance remain with the students. Use a feature branch and teammate
review before merging; do not treat this experiment as approval to replace the
application's heuristic.
