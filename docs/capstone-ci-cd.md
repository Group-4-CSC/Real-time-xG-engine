# CI/CD capstone evidence and submission checklist

Deadline supplied by the assignment: **November 9, 2026, 11:59 PM Eastern**.
Do not claim local checks as GitHub checks or merge without the owner's approval.

## Current repository and delivery verification (November 9, 2026, Eastern)

This is the current, independently checked GitHub status, replacing the original pre-CI inspection narrative. Historical PRs and earlier validation results remain documented below; do not mistake old checklists for the current submission state.

- **Repository:** [Group-4-CSC/Real-time-xG-engine](https://github.com/Group-4-CSC/Real-time-xG-engine) is public; the updated root [README](https://github.com/Group-4-CSC/Real-time-xG-engine/blob/main/README.md) is published.
- **Workflow:** [`.github/workflows/ci-cd.yml`](https://github.com/Group-4-CSC/Real-time-xG-engine/blob/main/.github/workflows/ci-cd.yml) runs on every push and every pull request to `main`. Four named jobs run in order: **Setup → Dependencies → Test → Deploy**. Deploy runs only after a successful push to `main`.
- **Latest verified successful `main` run:** [42749156649](https://github.com/Group-4-CSC/Real-time-xG-engine/actions/runs/42749156649) after [PR #45](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/45) was approved and merged. Setup, Dependencies, Test, and Deploy all concluded **success**.
- **Test job evidence:** [Test in run 42749156649](https://github.com/Group-4-CSC/Real-time-xG-engine/actions/runs/42749156649/job/129608668359) reports **51 analytics Python tests**, **9 Django API tests**, and **17 frontend Node tests**, all passing; frontend lint/build and the dataset smoke check completed. The smoke check processed **429 shots**. These are CI-run checks of the current combined code; they are not retroactive checks on older PRs.
- **Deployment:** [Deploy job](https://github.com/Group-4-CSC/Real-time-xG-engine/actions/runs/42749156649/job/129608972317) reported success and emitted [the GitHub Pages URL](https://group-4-csc.github.io/Real-time-xG-engine/). GitHub Pages serves **the React static demo only**—not Django, MongoDB, a live AI service, or live Python inference. A person must still open the URL in a signed-out/private browser to confirm public access and exercise the UI.
- **Protection:** The active `main-review-and-ci` ruleset (GitHub ruleset ID 26821342) targets the default branch; it has **no bypass actors**, requires a PR with **one approving review** and the GitHub Actions **Test** status check, dismisses stale approvals on new pushes, and disallows force pushes and branch deletion. Direct pushes to `main` are blocked by the required-PR rule.
- **Reviewed/merged PR evidence:** [#32—CI/CD and analytics acceptance tests](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/32) was approved by Rory with passing PR CI; [#38—Match Summary](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/38) and [#45—Shot Map tests](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/45) were approved by Alejandro; [#43—CSV preview](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/43) and [#44—Coach Dashboard](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/44) were approved by Rory. All are merged, with green PR Test checks.
- **Known verification gap:** A successful Pages deployment does not prove the entire full-stack app is hosted. Public Kanban visibility, browser behavior, and an unlisted video sharing link need manual signed-out checks before submission.

## Two GitHub delivery epics and nine tracked user stories

The live epic issues are [#33—Soccer Data Processing & xG Analytics](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/33) and [#34—Coach Dashboard & Match Visualization](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/34). Together their currently described deliverables map to **nine story issues**, grouped four and five. The older eight-story planning snapshot is superseded by this map. Open issues are not automatically failures, and closed issues do not on their own establish that every original acceptance criterion was met.

### Epic #33 — Soccer Data Processing & xG Analytics (four stories)

| Story and GitHub status | Implemented code / related PR | Automated acceptance proof and remaining gap |
| --- | --- | --- |
| [#35: Shot distance and angle](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/35) — **open** | [PR #20](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/20), approved and merged | `Analytics/test_acceptance.py` — `GeometryStoryAcceptanceTests` checks penalty-spot distance/angle and invalid positions; Alejandro added issue evidence comment. Close after teammate verifies criteria and board mapping. |
| [#3: Calculate shot xG and handle unsupported shots](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/3) — **closed** | [PR #22](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/22), [PR #28 API integration](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/28) | `XGStoryAcceptanceTests` plus API numeric/null/invalid-input tests; unsupported outside-model shots yield missing xG, not zero. **Original issue's database-persistence and every-shot wording is not fully implemented**; model covers supported penalty-area shots. |
| [#36: Convert StatsBomb data to shot CSV](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/36) — **closed** | Earlier team data import work, including [PR #18](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/18); exact issue-to-PR linkage needs confirmation | Dataset smoke processes 429 shot records, but a dedicated acceptance test explicitly proving every required export column and blank xG on unsupported rows was **not independently verified**. Ask the data owner to link the converter and test evidence. |
| [#2: Validate uploaded data](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/2) — **closed** | Existing frontend and backend validation in [PR #19](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/19) / [PR #28](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/28); [PR #43](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/43) tests local CSV validation for related story #41 | API tests reject invalid data; frontend tests reject malformed or invalid input. **Original criterion for a report listing each error is not fully demonstrated**; do not equate UI-first-error handling with a complete error report. |

### Epic #34 — Coach Dashboard & Match Visualization (five stories)

| Story and GitHub status | Implemented code / related PR | Automated acceptance proof and remaining gap |
| --- | --- | --- |
| [#41: CSV validation and preview (local demo)](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/41) — **closed** | [PR #43](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/43), teammate-approved and merged | `frontend/src/utils/csv.test.js` checks valid previews, optional xG, quoted names and invalid rows. Browser-local data only, not database storage. |
| [#42: Coach Dashboard metrics](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/42) — **closed** | [PR #44](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/44), teammate-approved and merged | `frontend/src/utils/dashboardMetrics.test.js` checks team/match/player totals, switching, missing and unsupported xG; no persistent player history is claimed. |
| [#11: Interactive shot map](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/11) — **closed** | [PR #21](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/21) and [PR #45](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/45), teammate-approved and merged | `frontend/src/components/vizShared.test.js` checks outcome labels, unique shot keys and team colors. These are **helper tests**, not complete rendered-map/browser acceptance proof; confirm the map visually. |
| [#12: Player/half filters](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/12) — **open** | [PR #21](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/21) implements map filters | `vizShared.test.js` checks period matching; browser validation is needed to confirm markers actually respond to selected player and half filters. Close only after acceptance sign-off. |
| [#37: Match Summary compares goals and xG](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/37) — **closed** | [PR #38](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/38), approved by Alejandro and merged | `vizShared.test.js` checks team goals, differential, excluded unsupported xG, partial coverage and pending display. A helper-level test is not a claim of a complete rendered-browser test. |

### Legacy issues and scope honesty

- [#1: Full CSV upload and match-record storage](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/1) is **closed**, but GitHub Pages only supports browser-local CSV import/preview. A Django/MongoDB persistence workflow is not verified; #41 is explicitly narrower.
- [#4: Team aggregate xG / xGD](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/4) is **open**; calculations and visuals exist, but reconcile the story acceptance evidence and actual completion before closure.
- The original broader backlog (#5–#10 and other older work) is not claimed complete merely because the two current delivery epics focus on nine selected stories.
- Historical implementation PRs generally predate the new required CI workflow. They establish reviewed code history, **not** retroactively passing required Test checks. The current combined implementation passes CI, and new story PRs have separate genuine approval and Test evidence.
- The coach demo is not a full production deployment. No secure live login, hosted MongoDB, backend persistence, or real hosted AI response should be claimed.

## GitHub workflow, branch protection, and security configuration

The course's required infrastructure settings are **verified active**, not pending administrator setup:

1. A single workflow named **xG Insights CI/CD** runs on all pushes and PRs to `main`; the four jobs are Setup, Dependencies, Test, and Deploy. The Test job fails on failed prerequisites and does not silently ignore test failures.
2. The active `main-review-and-ci` ruleset protects the default branch. It requires a pull request, at least one teammate approval, an up-to-date **Test** check from GitHub Actions, and no bypass actors. Force pushes and deletion are blocked; the broad restrict-updates rule is not enabled.
3. GitHub Pages is enabled with deployment through GitHub Actions. Deploy receives only Pages/OIDC write permissions and runs on successful trusted pushes to `main`. PR jobs have read-only permissions and do not deploy or receive production credentials.
4. The workflow scans accessible Git history and files using the pinned/scoped Gitleaks setup documented below. Secret-scan success does not prove that every external service is credential-free. Real secrets must be kept in Actions/environment secrets or ignored local configuration, never in the frontend build.
5. A reviewer should verify each new PR has a genuine approval and successful Test check **before** merging. Do not bypass the ruleset to rush submission.

GitHub Pages URL verified from the latest Deploy job: https://group-4-csc.github.io/Real-time-xG-engine/ . Public browser loading must still be checked separately.

## Secret-scan audit

Gitleaks **8.24.3** was downloaded from its official release, with SHA-256
verification retained. The script pins the validated archive checksum. The scan
covered the non-shallow checkout's reachable history with `--all --full-history`
(initially 47 patch-bearing commits / 70 Git commits including merges). After
fetching all 17 remote branch heads, the expanded scan passed over 53
patch-bearing commits / 77 reachable Git commits, including this feature branch,
and tracked/unignored files in the working tree, excluding ignored caches.
It does not establish that deleted/unreachable server-side objects or external
services contain no secrets.

Initial default-rule scans found 546 historical and 273 working-tree generic-key
matches. Every match was individually classified from its source line: public
StatsBomb `key_pass_id` UUID event references in the raw shot JSON files. No
values were printed. `.gitleaks.toml` retains all default rules and adds one
AND-scoped exception: that specific field/UUID format, the raw shot-data path,
and only the generic-api-key rule. No dataset directories were excluded. A synthetic detector control confirmed
that the exception permits a correctly formatted event UUID while default rules
still flag a generic credential-like value elsewhere; it was not a real credential.
With that reviewed configuration, both history and source scans passed with zero
remaining findings. This is a scoped scan result, not a guarantee that no secret
can exist. No real credential was identified and no credential rotation is
currently prescribed. The sample Django local-development key is not a
production credential; never reuse it for a hosted backend.

To reproduce on Linux x86_64:

```bash
bash scripts/scan-secrets.sh
```

If a future scan finds a real credential, do not paste its value into an issue.
Record only its path/line and commit ID, revoke or rotate it at its provider,
update the secure binding, audit access, and coordinate history cleanup with all
collaborators. Rewriting Git history requires separate approval and does not
replace revocation. Never bypass the scan merely to obtain a green check.

## Validation and remaining proof

### Latest remote CI — verified after PR #45 merge

- [Latest green `main` run #42749156649](https://github.com/Group-4-CSC/Real-time-xG-engine/actions/runs/42749156649): **Setup, Dependencies, Test and Deploy passed**.
- The [Test job](https://github.com/Group-4-CSC/Real-time-xG-engine/actions/runs/42749156649/job/129608668359) reports **51 Python analytics tests**, **9 Django API tests**, and **17 frontend Node tests** passing (**77 total**). Lint and build succeeded; the real-data smoke check processed **429 shots**.
- The [Deploy job](https://github.com/Group-4-CSC/Real-time-xG-engine/actions/runs/42749156649/job/129608972317) reports successful GitHub Pages publication at https://group-4-csc.github.io/Real-time-xG-engine/ .
- [PR #45](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/45) was approved by a teammate, passed its [PR workflow](https://github.com/Group-4-CSC/Real-time-xG-engine/actions/runs/42748371448), and was merged before this `main` run. [PR #32](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/32) is also approved/merged with a passing PR Test check.
- CI checks are **unit/helper/API acceptance checks**, not a complete end-to-end test of hosted database storage, authentication, browser UI, or hosted LLM integration. No MongoDB deployment/integration claim is made.
- Some old pre-CI PRs were approved and merged before GitHub Actions existed; the new workflow cannot manufacture historical Test checks for them.
- Manual items outstanding: open the Pages site and the Kanban project signed out, validate relevant browser UI behaviors, reconcile story statuses/links on the board, and verify the demonstration video link and length.

## Submission checklist — current status

- [x] **Public GitHub repository:** https://github.com/Group-4-CSC/Real-time-xG-engine .
- [x] **Updated root README published on main:** https://github.com/Group-4-CSC/Real-time-xG-engine/blob/main/README.md . A cosmetic extra `**` remains in the Verified Deployment heading; this does not invalidate the repository link.
- [x] **Successful four-stage CI/CD on `main`:** https://github.com/Group-4-CSC/Real-time-xG-engine/actions/runs/42749156649 . All four jobs passed; 77 automated tests passed.
- [x] **Merged PR with genuine teammate approval and passing PR Test:** https://github.com/Group-4-CSC/Real-time-xG-engine/pull/45 . Its successful [PR-associated workflow is here](https://github.com/Group-4-CSC/Real-time-xG-engine/actions/runs/42748371448). Additional example: [#32](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/32).
- [x] **Branch-protection ruleset:** `main-review-and-ci` is **Active**, targets `main`, requires one approval and passing `Test`, and has no bypass actors.
- [x] **Successful GitHub Pages deployment:** https://group-4-csc.github.io/Real-time-xG-engine/ — confirmed by the Deploy job logs. **Frontend-only**; not a deployed backend/database/LLM.
- [x] **Two epic issues and nine mapped story issues exist:** [Epic #33](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/33) and [Epic #34](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/34). This document links stories, implementation PRs, and test evidence while honestly naming partial criteria.
- [ ] **Kanban visibility and status:** https://github.com/orgs/Group-4-CSC/projects/1 — board was reported public in prior inspection, but the team should open it signed out and confirm all nine story items, assignments, and statuses are visible.
- [ ] **Resolve outstanding acceptance/status gaps:** issues [#35](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/35), [#12](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/12), and [#4](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/4) are open. Confirm tests and sign-off before marking any done. Also reconcile original closed issues #1/#2/#3 with their unimplemented full criteria.
- [ ] **Public demo smoke check:** open the deployed website in a signed-out browser and exercise demo entry, dashboard, map, filters, CSV validation and match summary. Do not substitute green Deploy for a live-browser check.
- [ ] **Three-minute video:** record, upload to YouTube as **unlisted**, confirm length is at most three minutes, and obtain the actual URL. No verified video URL was found in repository documentation during this audit.
- [ ] **Submission accessibility:** check the repository/README, green workflow, reviewed/merged PR, Kanban board, and unlisted video links from a signed-out browser; submit the required URLs before the deadline.


### Three-minute demonstration plan

1. **0:00–0:25:** show the public repository/README, two delivery epics on the
   public board, and explain the frontend-only Pages scope.
2. **0:25–1:05:** show the actual four-job green Actions run. Open Test logs for
   analytics, Django, and frontend checks. Show main-only Deploy and the environment URL.
3. **1:05–1:50:** open the real deployed URL signed out, choose Explore demo,
   show dashboard, Match Summary, Shot Map and player/half filters. Import sample
   CSV and show an invalid CSV error. Explain that data is local and AI is a placeholder.
4. **1:50–2:25:** show GEO-1/XG-1 acceptance tests, expected 11 m penalty-spot
   distance/36.8° angle, numeric supported xG, and unsupported `None`/API `null`.
   Explain outcome/provider-xG are not prediction features.
5. **2:25–3:00:** show the final PR's teammate approval and passing Test check,
   then branch rules and redacted secret-scan result. State remaining limitations
   and AI assistance. Verify the recording is under three minutes and publicly
   accessible to the grader. Never display tokens, real `.env` values, or secret panels.

Do not record green checks, approvals, or a deployment that have not actually
occurred. Obtain the owner's merge approval separately; this document is not it.
