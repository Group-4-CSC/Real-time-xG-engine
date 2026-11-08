# CI/CD capstone evidence and submission checklist

Deadline supplied by the assignment: **November 9, 2026, 11:59 PM Eastern**.
Do not claim local checks as GitHub checks or merge without the owner's approval.

## Inspection and existing work

Inspection started at `a21c675b28465a9531dd8086d613b7c2fd5d79be` on main.
The complete non-shallow checkout had 70 reachable commits, existing analytics,
Django API, React demo, dataset, and the merged experimental ML pipeline.
There was no `.github/workflows/` directory. Git fetch/remote reads work.

Anonymous GitHub HTML verifies the repository is public. Its Issues, PR, Actions,
and Projects pages were inspected without login. The API returns `Forbidden`
for repository metadata, branch protection, rulesets, issues, PRs, and Actions
runs. Therefore live protection settings are **unknown**, not assumed absent.
No administrative settings were modified. The GitHub PR-creation GraphQL
request was also denied (`Forbidden`). The feature branch was pushed; create
the PR manually using the summary/evidence in this guide (Codex also prepared a PR body outside
the checkout). The branch compare page
is https://github.com/Group-4-CSC/Real-time-xG-engine/compare/main...ci/capstone-pipeline-and-evidence?expand=1 . The public Actions page displayed its
getting-started screen and PR #31's Checks page displayed no historical checks.
There is no verified historical successful `Test` check on the old story PRs.
The new feature-branch workflow run below has now created a successful Test check.

Existing PR #23, **Refactor React Frontend and Add API Module**, is open. Its
proposed `frontend/src/api.js` is not in main and was not recreated here. Existing
PRs #18–#22 and #27–#31 already implement much of the assignment's functionality;
this change adds CI, tests, and evidence instead of duplicating those features.

## Two delivery epics and eight story evidence rows

These are **assignment delivery groupings**, not a claim that two new GitHub
Epic records or eight completed stories already exist. The original broader
project epics in the root README and the existing issue IDs are preserved.
The team must confirm this grouping with the instructor and represent it on
the board. The geometry story is extracted from the analytics owner's stated
responsibility and existing PR #20; a separate linked issue still needs creation.

For every row: the **current combined implementation passed Test** in
[run #1](https://github.com/Group-4-CSC/Real-time-xG-engine/actions/runs/42522809150),
commit `7f6cd5587f54fecc5ff74d5765512290b8483abc`. The
[Test job](https://github.com/Group-4-CSC/Real-time-xG-engine/actions/runs/42522809150/job/128860050078)
publicly reports **succeeded**. This does not retroactively add a passing check
to each historical PR or prove completion of missing functionality. The
public issue Development panels for #1, #2, #3, #4, #6, #11, and #12 say
“No branches or pull requests.” The PRs below are verified related implementations,
not invented formal issue/PR links. Add explicit references in issue comments or
PR descriptions; a merged PR alone does not prove that acceptance criteria passed.

### Epic A — trustworthy shot data and chance calculation

| Story | Functionality now | Related branch / PR and verified teammate approval | Acceptance evidence and gap |
| --- | --- | --- | --- |
| [US-1.1 / #1: CSV upload](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/1) | Partial: browser parses/previews/imports; no backend upload or persistent match storage | `feature/team-player-dashboard`, [PR #19](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/19), approved by anderc1-debug Oct 14 | Local browser smoke covers sample import; full issue criterion (stored shots linked to match) is not met. Formal issue/PR link missing. |
| [US-1.2 / #2: reject invalid data](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/2) | Partial: frontend rejects invalid file; API validates fields; offline ML loader validates IDs | PR #19 (above); `feature/football-xg-backend`, [PR #28](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/28), approved by alejops2005 Oct 17 | Browser smoke rejects missing columns; API `test_rejects_missing_or_invalid_shot_fields`; ML input-safety tests. Issue asks for a report listing each error; current browser stops at the first error. Formal link missing. |
| GEO-1: physical shot distance and angle (analytics owner) | Implemented: reused geometry in meters/degrees and input validation | `feature/xg-feature-engineering`, [PR #20](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/20), approved by anderc1-debug Oct 14 | Automated `GeometryStoryAcceptanceTests` in `Analytics/test_acceptance.py`: penalty-spot distance/angle and invalid coordinates; existing boundary/symmetry/goalpost tests retained. Separate story issue/link missing. |
| [US-2.1 / #3: xG and unsupported shots](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/3) | Implemented heuristic/API with missing unsupported values; offline logistic experiment. Partial against original issue's “every shot” and database-save criterion | `feature/xg-feature-engineering`, [PR #22](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/22), approved by anderc1-debug Oct 15; PR #28 API integration; `analytics/experimental-logistic-xg`, [PR #31](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/31), approved by anderc1-debug Nov 2 | Automated `XGStoryAcceptanceTests` plus API numeric/null/invalid-input tests. Issue is closed, but database persistence is not implemented and model scope is penalty-area only. Reconcile acceptance wording with team; do not claim full original criterion. Formal link missing. |

### Epic B — explain match and player performance

| Story | Functionality now | Related branch / PR and verified teammate approval | Acceptance evidence and gap |
| --- | --- | --- | --- |
| [US-2.2 / #4: team xG and xGD](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/4) | Implemented partial/supported totals in Match Summary; offline smoke totals; dashboard uses its own pending-total behavior | `feature/shot-map-match-summary`, [PR #21](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/21), approved by alejops2005 Oct 14; `feature/analytics-data-validation`, [PR #27](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/27), approved by anderc1-debug and jpor12 Oct 17 | New Node helper test verifies supported totals/coverage; dataset smoke checks team/match sums. Browser summary visited; full visual xGD acceptance still needs teammate sign-off. Formal issue/PR link missing. |
| [US-6.1 / #11: interactive shot map](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/11) | Implemented with team colors, outcome markers, details, and match selection | PR #21 (above) | New Node test covers stable team colors; browser smoke opens map. Hover/keyboard details still need complete manual acceptance. Formal link missing. |
| [US-6.2 / #12: player/half filters](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/12) | Implemented in Shot Map, with reset | PR #21 (above) | New Node test covers period selection; browser smoke exercises filter selections/reset. Helper tests are not full rendered-map assertions; teammate should confirm only matching markers remain. Formal link missing. |
| [US-3.2 / #6: player xG ranking](https://github.com/Group-4-CSC/Real-time-xG-engine/issues/6) | Partial: dashboard player totals and summary sorting exist; required selected-date-range ranking is missing | PR #19 (above); PR #21 (above); PR #23 remains open and must not be counted as merged | No full acceptance test for date-range ranking. Do not mark the issue complete. Formal link missing. |

Other original stories (#5 history, #7 comparison, #8 PDF, #9 roles, #10 secure
login) remain outside this delivery grouping and are not claimed implemented.
Team approval evidence above was read on public PR conversation pages, separately
from Git merge messages. Merged state and approvals are verified. The new feature-branch Test passed;
the old PRs have no verified historical required check. Do not manufacture
retroactive workflow evidence.

Manual board action: create two parent epic issues using the grouping titles above,
create a GEO-1 issue with the two geometry acceptance scenarios, and link the eight
story rows as sub-issues or explicit issue references. Attach the related PR links
and acceptance evidence. Keep partial stories open and mark missing CI/review proof
honestly; PR #31 alone is not evidence for unrelated frontend stories.

## Required GitHub settings

An administrator must perform these steps because the API cannot inspect or
modify them from this environment. Preserve existing stronger rules.

1. **Settings → Actions → General:** enable Actions and permit the pinned GitHub
   actions used in `.github/workflows/ci-cd.yml`. Keep default workflow token
   permissions read-only; Deploy explicitly requests only Pages/OIDC permissions.
2. Push this feature branch and open a PR targeting main. The workflow runs for
   the branch push and main-targeting PR. In **Actions**, open **xG Insights CI/CD**
   and wait for **Test** to succeed. Save the actual run URL. If the job fails,
   fix it and rerun; do not add a nonexistent/unproven required status check.
3. **Settings → Rules → Rulesets → New branch ruleset:** name it `main-review-and-ci`,
   target `main`, set enforcement **Active**, and leave the bypass list empty.
   Enable **Require a pull request before merging**, require **1 approval**,
   dismiss stale approvals on new commits, require resolved conversations,
   block force pushes, and restrict deletions. Requiring PRs without bypasses
   blocks ordinary direct pushes. Do not enable “Restrict updates” for everybody,
   which can also prevent normal PR merges.
4. **Only after step 2 has produced a successful Test check**, enable **Require
   status checks to pass**, select **Test** from the GitHub Actions app, and
   require branches to be up to date. Save the rule and verify it on a PR.
   If using classic **Settings → Branches → Add branch protection rule** instead,
   target `main`, choose the equivalent settings, check **Do not allow bypassing
   the above settings** (including administrators), and leave force pushes and
   deletions disabled. Have a teammate verify that direct pushes are blocked.
5. **Settings → Pages → Build and deployment → Source: GitHub Actions**.
   Configure the `github-pages` environment to allow only main deployments.
   PR jobs never receive deployment permissions or secrets. No personal token
   is required for Pages; GitHub supplies a short-lived token/OIDC identity.
6. Get a real teammate review of the final PR revision. Merge only after the
   project owner explicitly approves merging and all required checks pass.
   The merge's main push runs all four jobs and publishes the tested demo artifact.
   Open the actual Deploy environment URL while signed out and exercise the demo.

The workflow installs dependencies again in Test because jobs do not share
installed environments. `needs` orders Setup → Dependencies → Test → Deploy.
Test also runs after a failed/cancelled Dependencies job so its first gate fails
instead of allowing a skipped required check. Each automated command preserves
its failure exit status. Deploy is limited to successful pushes to main and
uses the artifact created by that same run's Test job; no PR artifact is deployed.

Pages is a static demo, not the full stack. No Django, MongoDB, AI provider,
authentication service, or Python prediction server is deployed. On Pages the
AI summary reports unavailability; no API credential should be embedded in Vite.
A production full-stack host and secure database/service setup are future work.

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

Local Linux validation on this feature branch:

- Python 3.12 / Node 24 dependencies installed; `pip check` passed.
- Analytics suite: **51 passed**, including five new story acceptance scenarios.
- Django `check` and API suite: **9 passed**; unused database setup skipped by
  Django because tests use `SimpleTestCase`, not a MongoDB integration claim.
- Frontend Node helper suite: **4 passed**; lint and production Pages-base build passed.
- Dataset smoke: **429 processed, 247 numeric, 182 unsupported, zero errors**.
- `actionlint` validated the workflow. GitHub workflow run #1 also completed
  successfully in 1m 31s; its Test job succeeded in 30s. Deploy was skipped as
  designed on a feature push. The public job page reports a nonblocking Node 20
  deprecation warning for the pinned action runtimes; GitHub ran them on Node 24.
- Live development WSGI requests passed for health, numeric xG, and unsupported
  API null. This still does not establish database readiness.
- Chromium browser smoke against the production build passed: Pages-base asset
  loading, demo entry, dashboard, summary, expected API-unavailable fallback, map
  filter selection/reset, invalid CSV rejection, and sample import. No browser
  JavaScript errors occurred. This is not proof that Pages has been published.
  The local preview command must pass the same base path as the build; omitting
  it initially caused missing JavaScript assets and was corrected.

The historical `PROTOTYPE_TESTING_CHECKLIST.md` records earlier results and
unchecked database/UI items. It is preserved as history, not presented as a
fresh acceptance sign-off. Full database migration/Atlas tests, rendered UI
acceptance for every story, and Windows execution remain unverified.

## Submission checklist

- [x] Public repository verified anonymously:
  https://github.com/Group-4-CSC/Real-time-xG-engine
- [ ] Updated root README published on main (URL exists, but this branch's new
  contents are not yet merged):
  https://github.com/Group-4-CSC/Real-time-xG-engine/blob/main/README.md
- [x] Green feature-push Actions run, verified on its public summary and Test
  job page:
  https://github.com/Group-4-CSC/Real-time-xG-engine/actions/runs/42522809150
  Test succeeded; Deploy correctly skipped. A green main run/deployment and a
  PR-associated check on the final revision still require the steps below.
- [ ] Merged PR with teammate approval **and passing new Test check**: still
  required. Historical [PR #31](https://github.com/Group-4-CSC/Real-time-xG-engine/pull/31)
  is merged and approved by anderc1-debug, but its Checks page has no successful
  required Test result, so it does not satisfy the combined requirement.
- [x] Public Kanban board loaded anonymously with story records:
  https://github.com/orgs/Group-4-CSC/projects/1
  (The older linked personal board is also public:
  https://github.com/users/anderc1-debug/projects/4.)
- [ ] Public deployment URL: obtain from the actual successful Deploy job's
  environment. The default Pages hostname could not be reached from this cloud
  environment (proxy 403); publication is **not verified**. Do not submit a
  guessed URL as a working deployment.
- [ ] Main protection verified after Test has first succeeded. Test has now
  succeeded in run #1, so an administrator can select it as a required check.
- [ ] Eight story rows reconciled with issue/PR links, acceptance criteria,
  teammate reviews, and actual CI results; incomplete stories remain disclosed.
- [ ] Three-minute video recorded and its sharing permissions tested signed out.

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
