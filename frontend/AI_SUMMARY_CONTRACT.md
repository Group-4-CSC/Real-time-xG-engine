# Sprint 3 AI Match Summary — frontend/API contract

Aligned with Michael's open backend PR #58 on November 17, 2026. This is a proposed contract until the backend PR is reviewed and merged.

**Endpoint:** `POST /api/ai/match-summary/` (JSON). Only Django calls the AI provider; never send keys from React.

Request (two distinct teams, one match and selected half):

```json
{
  "match_id": "M1",
  "half": "all",
  "teams": [
    {"name": "Home", "shots": 5, "goals": 1, "xg": 0.8,
     "xg_calculated_shots": 5, "xg_missing_shots": 0},
    {"name": "Away", "shots": 3, "goals": 0, "xg": 0.4,
     "xg_calculated_shots": 3, "xg_missing_shots": 0}
  ]
}
```

- `half` is `all`, `1`, or `2`.
- xG is `null` if no shots have a calculated xG (never use zero to mean missing).
- xG coverage counts must sum to each team's shots.
- The half selection changes the input statistics; do not imply a half's goals are the final score.

Successful response (HTTP 200):

```json
{"summary":"Three to five sentences about the supplied stats.", "is_placeholder":false}
```

The frontend accepts only a nonempty string `summary` and rejects `is_placeholder:true` so prototype text is never presented as AI output. The backend must validate the model's output and may later provide `is_fallback:true` or `source:"fallback"`. If a backend fallback is supplied, the frontend labels it as fallback, not AI-generated.

Failure (HTTP 400 for invalid input; HTTP 503 for provider failure; network/timeout errors): show a safe locally calculated **statistics-only fallback** based on the same supplied data. Never claim it came from the AI. Display a Retry button for manual retry. Do not send raw player free text or any API key to the provider.

**Owner split:** Shayaan — request client, UI, states, UI tests. Joseph/Michael — Python AI call, provider timeout and deterministic backend fallback. Alejandro — evaluation suite. Rory — CI Eval stage. Any eligible human teammate reviews PRs.

**Testing:** frontend tests mock network results; never call the actual AI provider. A later manual local integration demonstration must verify both generated and fallback cases against the merged Django endpoint.
