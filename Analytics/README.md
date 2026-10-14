# xG Insights: ML / Analytics

## 1. ML / Analytics Overview

xG Insights is a capstone project for measuring the quality of football shots and summarizing attacking performance. The project uses a React frontend, a Django and Django REST Framework backend, MongoDB through `django-mongodb-backend`, and a Python analytics / ML layer.

The ML / Analytics work is responsible for preparing shot data and developing and evaluating the xG calculation. The xG model is not finished: geometry feature calculations are implemented, but model training and saving xG predictions to MongoDB have not been implemented as part of the current work.

Shot locations use normalized full-pitch coordinates from 0 to 100 on both axes. Every shot is represented as attacking toward `x = 100`, with the opponent's goal centered at `y = 50`. Geometry converts these coordinates using a provisional 105 x 68 meter reference pitch. These dimensions are a consistent basis for calculating distances and angles, not a claim that every real-world stadium has exactly those dimensions.

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

### User Story 1: xG for supported penalty-area shots

As an analyst, I want the initial system to calculate an xG value for supported penalty-area shots so that I can measure shot quality beyond just goals scored.

**Acceptance criteria:**

**GIVEN** a stored shot event with valid location and supported features inside the attacking penalty area

**WHEN** the xG engine processes it

**THEN** a numeric xG value between 0 and 1 is generated and saved to the database.

The initial model scope is penalty-area shots only; it does not assign xG to every shot across the pitch. Shots outside that supported area must not be assigned a fabricated xG of zero.

### User Story 2: Team xG per match

As a coach, I want to see aggregated team xG per match so that I can evaluate my team's overall attacking performance.

**Acceptance criteria:**

**GIVEN** all shots in a match have an xG value

**WHEN** the coach opens the match summary

**THEN** total team xG and xG differential (xGD) are displayed.

## 4. Current Implementation

`xg_features.py` contains `prepare_shot_features(x_coord, y_coord, body_part)`. It validates numeric x and y coordinates, rejects boolean coordinates, requires a string body part, converts coordinates to floats, and normalizes body-part text. It recognizes `left_foot`, `right_foot`, `head`, and `other`; unknown body parts are mapped to `other`.

`xg_geometry.py` implements attacking penalty-box eligibility, distance to the goal center, and the angle between the physical goalposts. Geometry functions validate normalized coordinates and work across the full pitch. `calculate_shot_angle()` returns `None` at either physical goalpost because the angle is mathematically undefined there; invalid coordinates still raise `ValueError`.

These modules provide input preprocessing and geometry only. The xG model and saving predictions are not implemented.

## 5. Automated Testing

The preprocessing and geometry tests use Python's built-in `unittest` framework; no additional testing library is required. Run them from the repository root with:

```powershell
py -m unittest discover -s Analytics -p "test_*.py"
```

The suite covers feature preprocessing, penalty-area eligibility and its inclusive boundaries, distance and angle calculations (including symmetry and positions outside the penalty area), undefined goalpost angles, finite angles near the goalposts, and invalid coordinate rejection. The geometry functions are implemented, and the suite now includes geometry tests in addition to the original preprocessing tests.

## 6. Backend Integration

The backend currently exposes `POST /api/xg/calculate/`. Its xG calculation is temporary and hard-coded; it is not the final xG model and should not be treated as a trained or approved analytics calculation.

The future `compute_xg(shot)` integration must handle a `None` angle (for a shot exactly at a goalpost) without crashing the entire CSV processing workflow. Invalid coordinates must still be rejected. Shots outside the initial model's supported penalty area must not receive a fabricated xG of zero. The Django import path and Python packaging arrangement for importing Analytics still need to be agreed with Joseph; these backend integration changes are not implemented here.

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

The current geometry convention is normalized 0-100 full-pitch coordinates, with all shots attacking toward `x = 100`, and a provisional 105 x 68 meter reference pitch for geometry calculations. The team must still agree on these data and integration details:

- Exact CSV shot fields
- MongoDB shot structure
- Django import path and Python packaging arrangement with Joseph
- API / analytics interface, including how unsupported-area shots are represented

## 8. Next Steps

1. Finalize review of the implemented geometry and automated tests.
2. Agree on exact CSV shot fields and MongoDB shot structure.
3. Define and implement the `compute_xg(shot)` contract for supported penalty-area shots, undefined goalpost angles, and invalid coordinates.
4. Prepare historical shot data for the initial penalty-area model.
5. Train and evaluate a baseline xG model.
6. Agree on the Django import path and Python packaging arrangement with Joseph, then integrate the analytics model with the backend.
7. Save supported xG values to MongoDB.
8. Calculate team xG and xGD.
9. Support dashboard and shot-map analytics.

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

I personally reviewed the preprocessing and geometry code, checked its scope against the requirements, and reviewed the automated tests. Run the test command in Section 5 to verify the current suite before submitting changes.

AI did not make project decisions or independently verify correctness. Generated code and tests require review and execution by the project team.

## 11. Git Workflow

Use a feature branch for this work and submit changes for pull request review before merging. Run the focused test command above and inspect `git diff` to confirm that changes stay within scope before committing. Documentation changes should also go through a feature branch, pull request, and teammate review.
