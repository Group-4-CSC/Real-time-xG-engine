# Issue #61 handoff: Jason, Michael, Rory

Inspected main `389ea50`, Issue #61, Issue #63, PR #58 (head from
`feature/real-ai-match-summary`), and PR #66 (head `3f579ea`). No backend or workflow
files were changed. The GitHub API returns Forbidden from this workspace; see
posting outcome in the final handoff rather than assuming messages were delivered.
The actual attempts to post an Issue #63 comment and a PR #66 comment both
returned Forbidden. The messages remain in this document for manual delivery.

## Jason — Issue #63

The existing three merged examples are preserved as JSON objects. This branch
adds twelve cases MS-04 through MS-15 following the merged coverage plan, with
schema unchanged. Every input and expected structured fact passes validation;
all 15 are marked `populated_pending_jason_review`, not human-approved.

Please review statistics, reference wording, and team-name pairs before merging.
No visible remote branch or linked Issue #63 PR contained alternate golden
fixtures at inspection time. If you have unpublished changes, reconcile them by
case ID rather than replacing either file wholesale. The runner pins response
snapshots to the dataset SHA-256 so changed fixtures require reviewed re-recording.

Your prompt-injection attack/result/mitigation and backend risk review remain
Issue #63 work. This PR does not close #63 or fabricate a provider attack result.
Treat user-controlled names as untrusted data; the adapter forwards them as data
and the checker escapes them for literal matching. That is not a claim the LLM
itself resists prompt injection. The backend owner should review name constraints,
prompt separation, and output validation independently.

## Michael — PR #58

`evals.adapter.to_backend(example, half='all')` maps to your inspected serializer:
`match_id`, `half`, and exactly two `teams` containing `name`, `shots`, `goals`,
`xg`, `xg_calculated_shots`, `xg_missing_shots`. Missing-shot count equals shots
minus supported_shots; missing xG stays null. The adapter does not import your
unmerged module or require Django. Tests exercise all cases and allowed halves.

Optional live calls POST to your endpoint and require `is_placeholder: false`.
Main's GET placeholder is not a valid live target. Your numeric whitelist can
accept a number attributed to the wrong team; the new evaluator tests that
specific failure. The evaluator's conservative text grammar is intentionally
narrow and will flag many otherwise valid live paraphrases for review. Agree
accepted wording/extensions with reviewed negative controls before interpreting
live failure rates. No backend/provider result is claimed by the mock run.

## Rory — PR #66

After installing `evals/requirements.txt`, Eval must run:

```bash
python -m unittest discover -s evals/tests -p 'test_*.py' -v
python -m evals.run_evals
```

The latter command evaluates actual response texts for all 15 originals plus
swapped-name variants, writes `evals/results/latest.json`, and exits **1** if any
case/output/pair fails. It is not a JSON-only validation check. Missing cases or
responses are hard failures. Default provenance is **mock**, not live provider.
Keep `python -m evals.dataset --require-complete` if desired, but remove its
`continue-on-error: true`. Do not use continue-on-error on the runner/tests.

Deploy must change from `needs: test` to `needs: eval` (or `[test, eval]`) while
retaining its main-push-only condition. A successful Test job alone cannot prove
Eval passed. Do not merge the informational completeness gate as a release gate.
Upload the result JSON with `if: always()` if artifacts are desired. Never run
`--mode live` or inject production LLM keys in PR CI. This runner refuses live
mode when CI/GITHUB_ACTIONS is set. Its default mock check guards evaluator
behavior and fixtures, **not live model drift**; schedule explicit live evaluation
separately on a trusted environment when the backend is available.

New eval unit tests include deliberately broken responses and assert a nonzero
runner return code; the test suite itself stays green when detection works.
Independent fixture and tone review remain outstanding, even on green CI.

## Recorded validation on this branch

- 32 evaluation unit tests passed, including nonzero CLI failure proofs.
- 51 analytics and 9 main-branch backend tests passed.
- 33 frontend unit tests passed; build passed. Existing frontend lint exited 0
  with three React-ref warnings in App.jsx; no frontend files were changed.
- All 45 adapted payloads (15 cases × three halves) were independently validated
  against the actual inspected PR #58 serializer, loaded without invoking its
  generator. This is a contract check, not a live-provider evaluation.
- Default mock run: 15 cases, 90 outputs, both automated case pass rates 100%,
  release_ready false. No provider results or independent human approval claimed.
- Actual negative CLI run: one response credited Falcons with 9 instead of 2
  goals. Process exited 1, overall_pass false; each case pass rate was 14/15.
  The negative result was saved outside the checkout, keeping latest.json as
  the reproducible positive mock baseline.
