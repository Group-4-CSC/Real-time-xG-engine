# xG Insights: ML / Analytics

## 1. ML / Analytics Overview

xG Insights is a capstone project for measuring the quality of football shots and summarizing attacking performance. The project uses a React frontend, a Django and Django REST Framework backend, MongoDB through `django-mongodb-backend`, and a Python analytics / ML layer.

The ML / Analytics work is responsible for preparing shot data and, in a later step, developing and evaluating the xG calculation. The xG model is not finished. Distance and angle feature calculations, model training, and saving xG predictions to MongoDB have not been implemented as part of the current work.

## 2. Responsibilities

The ML / Analytics responsibilities are to:

- Alejandro (ML / Analytics) owns the xG calculation and analytics logic.
- Joseph (backend) owns Django and Django REST Framework API work.
- Jason (database) owns MongoDB structure and database-related work.
- Validate and normalize shot inputs.
- Agree on the data conventions required for feature engineering.
- Develop and test shot features and the xG model.
- Evaluate the model and provide xG results for backend integration.
- Support match-level team xG and xGD calculations and analytics for the dashboard and shot map.

## 3. User Stories

### User Story 1: xG for every shot

As an analyst, I want the system to calculate an xG value for every shot so that I can measure shot quality beyond just goals scored.

**Acceptance criteria:**

**GIVEN** a stored shot event with location, angle, and body part

**WHEN** the xG engine processes it

**THEN** a numeric xG value between 0 and 1 is generated and saved to the database.

### User Story 2: Team xG per match

As a coach, I want to see aggregated team xG per match so that I can evaluate my team's overall attacking performance.

**Acceptance criteria:**

**GIVEN** all shots in a match have an xG value

**WHEN** the coach opens the match summary

**THEN** total team xG and xG differential (xGD) are displayed.

## 4. Current Implementation

`xg_features.py` contains `prepare_shot_features(x_coord, y_coord, body_part)`. It validates numeric x and y coordinates, rejects boolean coordinates, requires a string body part, converts coordinates to floats, and normalizes body-part text. It recognizes `left_foot`, `right_foot`, `head`, and `other`; unknown body parts are mapped to `other`.

This is input preprocessing only. It does not calculate shot distance, shot angle, or xG, and it does not save predictions.

## 5. Automated Testing

The preprocessing tests use Python's built-in `unittest` framework; no additional testing library is required. Run them from the repository root with:

```powershell
py -m unittest discover -s Analytics -p "test_*.py"
```

The 9 tests cover valid numeric coordinates, integer-to-float conversion, normalization of `Right Foot` to `right_foot`, normalization of `HEAD` to `head`, mapping an unknown body part to `other`, invalid x and y coordinates, invalid body-part types, and boolean coordinate rejection. All 9 tests currently pass.

## 6. Backend Integration

The backend currently exposes `POST /api/xg/calculate/`. Its xG calculation is temporary and hard-coded; it is not the final xG model and should not be treated as a trained or approved analytics calculation.

The intended architecture is:

```text
Django / DRF API
    -> ML / Analytics module
    -> trained/final xG calculation
    -> result returned to backend
    -> result stored in MongoDB
```

Joseph (backend) owns Django and Django REST Framework API work. Jason (database) owns MongoDB structure and database-related work. Alejandro (ML / Analytics) owns the xG calculation and analytics logic. The intended architecture is not yet fully implemented.

## 7. Decisions Still Needed

The team must agree on these data and integration details before feature engineering continues:

- Shot coordinate convention
- Pitch dimensions
- Attacking direction
- Goal location
- Exact CSV shot fields
- MongoDB shot structure
- API / analytics interface

No assumptions about these conventions have been made here.

## 8. Next Steps

1. Finish and merge preprocessing tests through PR review.
2. Confirm shot coordinate convention.
3. Add shot distance feature.
4. Add shot angle feature.
5. Add automated tests for feature engineering.
6. Prepare historical shot data.
7. Train/evaluate a baseline xG model.
8. Integrate the analytics model with the Django backend.
9. Save xG values to MongoDB.
10. Calculate team xG.
11. Calculate xGD.
12. Support dashboard and shot-map analytics.

## 9. AI-Assisted Development

GitHub Copilot has been used for:

- Generating the initial preprocessing implementation from detailed requirements.
- Drafting automated unit tests.

ChatGPT has been used for:

- Breaking ML work into smaller development tasks.
- Helping create detailed Copilot prompts.
- Reviewing generated code and tests.
- Explaining Python concepts.
- Planning Git / GitHub workflow.
- Identifying backend / analytics integration questions.

AI tools supported the development process; project decisions remain the team's responsibility.

## 10. AI Verification

I personally reviewed the generated preprocessing code, checked its scope against the requirements, manually tested the preprocessing behavior, and reviewed all generated automated tests. I confirmed that production code was not changed by the test task, ran all 9 tests locally, and inspected Git diffs before committing.

AI did not make project decisions or independently verify correctness. Generated code and tests were reviewed and run by me.

## 11. Git Workflow

Use a feature branch for this work and submit changes for pull request review before merging. Run the focused test command above and inspect `git diff` to confirm that changes stay within scope before committing. Documentation changes should also go through a feature branch, pull request, and teammate review.
