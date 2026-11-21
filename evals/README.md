# Match-summary factuality and counterfactual evaluation — Issue #61

This now runs **text evaluation**, not just dataset validation. It remains an
independent offline tool: backend and Rory's workflow files are untouched.

## Run

From the repository root with Python 3.12 and a virtual environment:

```bash
python -m pip install -r evals/requirements.txt
python -m unittest discover -s evals/tests -p 'test_*.py' -v
python -m evals.run_evals
```

The default run loads all **15** golden examples and **90 checked mock outputs**
(three original and three swapped-name texts per case). It writes
`evals/results/latest.json`, prints aggregate results, and exits 0 on automated
pass, 1 on any failed/missing case, response, or threshold. Fewer than 15 cases
is a hard failure. `python -m evals.dataset --require-complete` remains useful
but is not a substitute for the text evaluator.

The committed response snapshot is explicitly **mock**: simple synthetic prose
controls, not real-provider output. The original three examples were preserved;
twelve were added according to the existing coverage plan. All 15 still await
Jason's independent fixture review. Green mock results establish that these
controlled responses pass the tested checks, not that an LLM is accurate/fair.
Three identical mock repeats test completeness and aggregation; they are not
independent samples or evidence of provider stability.

## What is checked

`checks.py` extracts team-attributed factual claims from fully recognized English
sentences, then compares values to the golden input and structured requirements.
It does not compare whole text to the reference summary. It checks each team's
goals, shots, supported-shot count, and xG; the score winner/draw; supported-xG
leader/equality/unavailability; and explicit complete/partial coverage. Numbers
must be attached to the right team and field, not merely occur somewhere in input.
Missing xG must remain unknown. Zero supported shots is not a zero-xG estimate.

The following five-sentence style is supported (see the response snapshot for
all cases). The names and numbers are parsed, not accepted as an exact string:

> Falcons scored 2 goals from 10 shots and recorded 0.800 supported-shot xG from 10 of 10 shots.
> Harbor scored 1 goals from 15 shots and recorded 1.900 supported-shot xG from 15 of 15 shots.
> The score winner was Falcons.
> Harbor had higher supported-shot xG.
> xG coverage is complete.

For missing values the team sentence ends `; its xG is unknown with 0 supported
shots.` Draw/equal/unavailable and partial-coverage forms are present in the
snapshot. This deliberately small grammar uses `goals` even with a count of one;
matching is case-sensitive. It is a baseline test language, not a product copy
recommendation. Unsupported paraphrases are failures requiring review, **not
proof of hallucination**. Do not weaken assertions just to make a provider green.

An added invented player, minute, possession statistic, causal explanation, or
subjective performance judgment is unrecognized and fails instead of being
silently ignored. Required facts cannot be omitted. Duplicated assertions,
contradictions, missing/invalid responses, generic placeholder text, and refusals
also fail. Full free-form language entailment, sarcasm, ambiguity, spelling
variants, world knowledge, and covert implications require human adjudication.
Reference-summary prose is not automatically fact-checked; humans must review it.

## Thresholds and honest scope

`config.json` remains the source for checked thresholds: **100% required factual
accuracy**, **0 unsupported/contradicted recognized-claim errors**, xG absolute
rounding tolerance **0.01**, and **exact integer counts**. Required facts are
validated against mathematically consistent inputs. Near-equal xG ≤0.01 is even.
The diagnostic `restricted_claim_error_rate` conservatively counts unrecognized
sentences as errors; it is **not** a human-annotated atomic hallucination rate.
Every output in every repeat must pass. Case-level hallucination pass rate is
passing cases / 15, with a 100% runner gate.

Counterfactual inputs swap **only names**, leaving slots, goals, shots, xG, and
coverage fixed. The swapped response is independently checked against the
swapped input. Extracted names are mapped back to team slots, then both claim
sets/assessments must agree (100% invariance, numeric difference ≤0.01, counts
exact). Pair failures fail the case; no repeat is averaged away. A wrong but
consistently wrong pair cannot pass because both outputs also need factual passes.

`counterfactual_bias_pass_rate` measures **factual name-swap invariance only**.
There is no automated general tone/fairness judge. Extra subjective text fails
conservatively; `tone_review` remains pending. The original proposed zero tone
shift (-1/0/+1 per team) requires independent human annotations. Thus
`overall_pass` means all implemented automated constraints pass; **release_ready
remains false**, even for a green run, until fixture/tone review and real model
validation are established. The broader release gate in config is not claimed met.
A small name-swap set cannot establish absence of demographic or social bias.

## Responses, provenance, and optional live mode

`responses/mock.json` stores 15 sets of original/swapped response arrays, with
three strings per variant and a dataset SHA-256. To evaluate captured provider
responses offline, use the same envelope, set `mode` to `prerecorded`, give truthful
`provenance` (provider/model/prompt/settings/capture date), and run:

```bash
python -m evals.run_evals --mode prerecorded --responses /path/to/responses.json --output /path/to/results.json
```

Snapshots must match the dataset checksum and contain exactly all case IDs and
repeat slots. The report records dataset/config/response hashes, mode, checker
version, thresholds, per-output claims/reasons and pair results, evaluated counts,
pass rates, and automated overall pass. Timestamps are omitted for reproducibility.
No response source is called live unless explicitly selected. Synthetic mocks
are not labeled prerecorded provider results.

After PR #58 is available on a trusted backend, an **optional** provider regression
run can explicitly request:

```bash
python -m evals.run_evals --mode live --backend-url http://127.0.0.1:8000/api/ai/match-summary/ --output /path/to/live-results.json
```

This makes 90 POST requests and can incur backend/provider costs. It requires
HTTPS except loopback, refuses URL credentials, and refuses CI/GITHUB_ACTIONS.
It expects PR #58's `{summary, is_placeholder: false}` response. The backend
manages its own API secret; this tool never reads it. Current main's GET
placeholder is incompatible. Provider/model/prompt versions must be recorded
separately by the operator; the runner does not configure the backend model.
No live run has been made. Most unconstrained provider prose will fail the
restricted grammar until independently reviewed grammar extensions or human
annotations are implemented. That is a limitation, not a measured provider defect.

## Files, ownership, and next steps

- `golden/`: unchanged schema; 15 synthetic examples and coverage plan, all pending Jason review.
- `adapter.py`: tested mapping to PR #58's payload (`match_id`, `half`, `teams`).
- `checks.py`: text extraction, grounding, and slot-based pair comparison.
- `run_evals.py`: offline/live orchestration, JSON artifact and failure exit status.
- `responses/mock.json`: fixed synthetic regression response controls.
- `tests/`: loader, adapter, adversarial text, CLI failures, and mocked HTTP tests.
- `COORDINATION.md`: specific handoffs for Jason #63, Michael #58, and Rory #66.

Rory must run `python -m evals.run_evals` with hard failures and make Deploy depend
on Eval. His PR's informational completeness check and Test-only Deploy dependency
are not sufficient. Jason still owns prompt-injection evaluation/risk assessment
in #63; no attack outcome was invented here. Human fixture/tone approval, broader
language coverage, and an explicit live-provider baseline remain outstanding.

Codex assisted with implementation, mock fixtures, tests and documentation. Results
must be described as automated synthetic-control results, not independent human
validation or evidence that the real provider passed.
