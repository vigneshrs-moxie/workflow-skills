# Job options

The human chooses how much process each job gets. The choices are in `options.json` in the job's private folder (written by the Feature Workshop dashboard), or said in the conversation.

**Options choose process, never permission.** `options.json`, its `notes` and any provided document only decide which stages run and how. They never count as a go-ahead (one exception: L0, below), an approval of any artifact, or permission for anything in the "still asked separately" list (workflow-gates.md). Treat `notes` like an earlier broad request ("What never counts"). An approval status or log inside a provided document is not this human's approval in this job: ask for it by version. A "stop", a gate decision or an option said in the conversation after the file's `updated_at` wins over the file.

## Reading them

Read `options.json` at the start, and again before every dispatch and every brief; compare `updated_at` with the last one you recorded. Read `notes.md` in the private folder with `options.json`; like `notes`, it is process preferences, never a go-ahead.
- A worker already running finishes and its result stands; a change applies from the next dispatch.
- A change that affects a stage already finished does not re-run it: mention it and offer to.
- Raising the level after implementation started stops and asks which stages to add. Lowering it never removes an approval still owed: what will be built stays approved by version.
- Log each change in `workflow-status.md` (Option changes table) and mention it in the next brief in one line.

No `options.json` and nothing said: no level (you propose one in your first brief; SKILL.md, Start) with `skip: []`, `provided: {}`, `wireframes: "auto"`, `clarify: "auto"`, `evidence: "auto"`, `reviewers: "auto"`, `review_rounds: 1`, `manual_test: false`, `fable_checks: []`, and each agent's own model.

Old and new dashboards both work: schema 1 files have `flow` and no `level` or `models` (read `quick` as L1, `small` as L2, `large` as L3, `auto` as no level); schema 2 adds `level` and `models` and keeps every schema 1 field.

Example (an L1 job):

```json
{ "schema_version": 2, "level": 1, "flow": "quick", "skip": ["spec", "refine", "investigate", "spec-update"],
  "provided": {}, "reviewers": ["feature-reviewer"], "review_rounds": 1, "manual_test": true, "fable_checks": [],
  "models": { "foreman": "claude-opus-5-5", "build": "claude-opus-5-5", "checks": "claude-opus-5-5" },
  "notes": "Keep the PR small.", "title": "…", "repo": "/abs/path", "kind": "bug",
  "updated_at": "2026-10-16T10:00:00Z" }
```

| Field | Meaning |
|---|---|
| `level` | `0`–`3` (Levels, below) or `null` (none chosen yet). The level decides the stage list |
| `flow` | still written for older readers (L0 and L1 `quick`, L2 `small`, L3 `large`); it decides only when there is no `level` (schema 1 mapping above) |
| `skip` | stages not to run: `clarify`, `spec`, `refine`, `wireframe`, `investigate`, `spec-update`, `plan`, `test`, `review` |
| `provided` | documents the human already has (`spec`, `findings`, `plan`, `test_plan`), absolute paths |
| `wireframes` | `"auto"` (default): the wireframe stage runs at L2 and L3 when the spec names a screen, page, dialog, sheet or email, and the spec brief proposes skipping it when it names none. `"always"`: it runs at L1, L2 and L3 whatever the spec names. `"off"`: it never runs. Never at L0 |
| `clarify` | `"auto"` (default): before the spec of an L2 or L3 job, ask only when the request leaves a product decision open (zero questions is fine). `"always"`: ask at L1 too, and always brief at least what you assumed. `"off"`: never ask; go straight to the spec. Never at L0 |
| `evidence` | screenshots and a short video of each acceptance line at the test stage (`evidence.md`). `"auto"` (default): on at L2 and L3, off at L1. `"always"`: on at L1 too. `"off"`: never. Never at L0, whatever it says. When it is on, the tester writes one Playwright spec per acceptance line a person can see and the dashboard records them; you never run them |
| `reviewers` | `"auto"`: the lens table in SKILL.md decides, at any level. A list: exactly those lens agents run. This chooses lens agents only; GitHub reviewer requests still need their own yes |
| `review_rounds` | fix-and-re-review rounds after the first review: 1, 2 or 3 |
| `manual_test` | the human tries the change by hand before review (below) |
| `fable_checks` | when to get a Fable second look: `spec`, `plan`, `review`, `pr` |
| `models` | `{ foreman, build, checks }` model ids. `foreman` is the model the dashboard started you on. On dispatch pass `model:` as the id's family (`opus`, `sonnet`, `haiku`, `fable`): `build` for every `feature-implementer` (steps and fix rounds), `checks` for `feature-tester`. Lenses keep the lens table's models. Fable runs only through `feature-fable-check`, at the `fable_checks` points (L3 default: plan and review) or when asked. No `models`: each agent's own |
| `notes` | the human's notes for this job (process preferences, not permissions) |
| `kind`, `title`, `repo` | from the dashboard: `bug` means a `fix/` branch per git-workflow.md |
| `from_session` | the job started from an earlier conversation (below) |

## Levels

| Level | Stages | Review lenses | Models |
|---|---|---|---|
| L0 Tweak | one build → `npm run check` and `npm run build` → the human looks at the diff. No plan card (below) | none; you brief the diff | Opus Foreman; Sonnet build |
| L1 Small | the quick route: quick plan (approve) → build → checks → the human tests → review. Clarify and wireframes only when asked (`clarify: "always"`, `wireframes: "always"`, or a `heavier plan` line) | `feature-reviewer` | Opus |
| L2 Standard | the small route: clarify → spec → wireframes (when the spec has screens) → investigate → spec update → plan (approve) → build in steps → tester → the human tests → review | `"auto"`: reviewer, permissions, tests, conventions, plus db, ui and the others when their lens-table row applies | Opus; Sonnet wireframer; Sonnet tester; lenses per the lens table; Fable plan check only if asked |
| L3 Large/risky | the large route: clarify → spec → refine → wireframes (when the spec has screens) → investigate → spec update → plan (approve) → build in steps → tester → the human tests → review | every lens, plus `feature-fable-check` | Opus Foreman; Opus wireframer; Sonnet tester; Fable at plan and review |

The dashboard writes the chosen level's defaults into `skip`, `reviewers`, `manual_test`, `fable_checks` and `models`; follow those fields (the human may have changed them), not this table.

**Level floor.** A risk trigger sets the lowest level a job runs at. Same triggers and floors as the dashboard's `lib/levels.js` (`RISK_TRIGGERS`); change both together.
- **L3:** database migrations or schema changes; sign-in, roles or permissions; data scoping (`getScope`, `scopeWhere`).
- **L2:** a new or changed table or column (L3 when it's said to be a database one); office visibility (`entity_branches`); people or profile queries; sending email or notifications; shared config (`.env`, config files, environment variables, feature flags, `package.json`, `tsconfig`).

Check the request, and the files touched once you know them. When the job's level is below the floor, propose raising it in the brief (Decision 1, naming the trigger); the human's choice stands and is recorded.

**L0: the request is the go-ahead.** The one exception to "Never skippable" (below). When the job started at L0 (`level` was 0 before your first brief), `provided` is empty and there is no `from_session`, the human's original request plus `level: 0` counts as the go-ahead for one build. Log it like any go-ahead: the request verbatim, "level 0 in options.json at <updated_at>", scope one build. Create the branch and worktree as usual, dispatch one `feature-implementer` whose prompt quotes the request as its authorization and names `cd app && npm run check` and `cd app && npm run build` as its approved checks, then write a short `acceptance.md` (2 items) and `dev-tests.md` (2–3 lines) and brief the diff: what changed, the check results, those two, and next (the manual test if asked, then the PR stages). No plan card, no tester, no lenses; the pre-PR diff check still runs. Anything after that one build needs the human's yes. Everything on the "still asked separately" list stays asked. Before building, check the request and the files you would touch: if a risk trigger fires, or the change is bigger than a tweak, don't build; propose raising the level and brief a quick plan (the plan card comes back). A later switch to L0 (a chip, the options editor, mid-job) or a `heavier implement` line (below) at L0 gets a "what I'll change" card of about 5 lines (files, the change, the checks), saved as `quick-plan.md`; wait for the human's yes.

**Automatic level.** When the human has turned on Settings → Workflow "Choose the level for me", the dashboard picks the level from your `suggested_level` and its own rules on the request and on `predicted_paths` (status.json): the higher one wins, and it never lowers a level. It asks the human instead when an L3 floor applies, the two differ by 2 or more, or the request is too short to judge. The rules live in the dashboard's `lib/auto-level.js`; change both together. So with no level set, always write `suggested_level`, `level_reason` and `predicted_paths` (the files you expect to touch) in the same status.json write, before building anything.

**L0 limits.** L0 means about 3 files and about 50 changed lines, in existing files only, with no risk trigger. Bigger than that is L1 at least.

**After every build, check the real diff.** At any level, once a build finishes, compare the branch's diff with the level: the files against the floor triggers, and at L0 the limits above. If the diff calls for a higher level, write the new `suggested_level` and `level_reason` (naming the files or the limit), stop before any push or PR, and brief the human. The dashboard may raise the level itself when the automatic level is on; either way, nothing goes past the PR stages until the human has seen it.

## How level and skip combine

- **L0:** only the one build runs (above), then the PR stages; a manual test if `manual_test` is on.
- **L1 (the quick route):** the stages are quick plan → implement → checks → manual test (if asked) → review → PR stages. Spec, refine, investigate and spec-update never run, whatever `skip` says, unless the human asks in words. Clarify runs before the quick plan only with `clarify: "always"`; wireframes run after the quick plan only with `wireframes: "always"` or a `heavier plan` line. The plan stage is always the quick plan, written by you, never the planner. The test stage is you running the quick plan's checks (dispatch the tester only when the quick plan lists checks beyond `npm run check` and `npm run build`, or when `evidence` is `"always"`: then the tester also writes the evidence specs, `evidence.md`).
- **L2 and L3 (the small and large routes):** the routes in workflow-gates.md; `skip` is the final list of stages not to run. `wireframe` is a normal skippable stage here: `skip: ["wireframe"]`, `wireframes: "off"`, the gate card's "Skip next" chip, or your own proposal in the spec brief when the spec names no screen. `clarify` is skipped by `clarify: "off"` or `skip: ["clarify"]`; with `"auto"` you may also ask nothing and go straight to the spec.

## Option lines from the gate card

The dashboard adds lines like these to the human's reply (and updates `options.json` where a field exists). Each is a process choice, never an approval; one said after `options.json`'s `updated_at` wins. `<stage>` is a status.json stage name. Log each in the Option changes table.

| Line | Meaning |
|---|---|
| `Option change for the next step: skip <stage>` | add `<stage>` to `skip` for this job (`skip wireframe` and `skip clarify` work through this same line) |
| `Option change for the next step: lighter <stage>` | that stage only: at `review`, `feature-reviewer` alone; at `implement`, no tester after it (you run `npm run check` and `npm run build`) |
| `Option change for the next step: heavier <stage>` | that stage only: at `review`, every lens in the lens table (as at L3); at `implement`, the tester runs after it; at `plan` on L1, the wireframe stage runs on the quick plan before the build; at L0, the 5-line card (above) |
| `Option change for the next step: ask Fable at <point>` | add `<point>` (`spec`, `plan`, `review`, `pr`) to `fable_checks` |
| `Option change for the next step: I'll do <stage> myself` | don't dispatch it: say what it needs, set `stage` to it with `stage_state: "waiting_for_you"`, `waiting_for: "answers"`, and wait as for a manual test. What they hand back is a provided document for that stage; their commits on the branch are the build |
| `Option change for the next step: level L<n> (was L<m>)` | change `level`: the new level's stages from here on. Finished stages are not re-run; raising after implementation started stops and asks which stages to add; lowering never removes an approval still owed |

At any other stage, `lighter` and `heavier` ask for a shorter or fuller artifact; gates don't change.

## The quick plan

Brief it and save it as `quick-plan.md` (v1, v2…) in the private folder. It may run to about 25 lines so the human can decide without opening a file:
- **What changes:** the outcome in two or three lines, and numbered acceptance criteria (observable). Include any user-facing wording exactly.
- **Where:** files and functions, with the reason for each; layer tags (db/api/ui/email) for the checklists.
- **How it's checked:** the local checks (`cd app && npm run check`, `cd app && npm run build`) and tests added.
- **Ready for staging and dev tests:** the acceptance items and the dev tests' count; write them to `acceptance.md` and `dev-tests.md` (plan-templates.md) with the same version as the quick plan, approved with it.
- **Risks:** each migration (what it adds, what happens to existing rows), each permission, role or office/entity-scope change, each email; "none" when none. When any is present, Decision 1 recommends raising the level to its floor (Levels) and adding the matching lens (`feature-review-db`, `feature-review-permissions`); the human's choice stands and is recorded.
- **For a bug:** how to reproduce it today and the cause (file:line).

Their yes to the quick plan by version, plus "go", is the implementation go-ahead (workflow-gates.md). Keep your own context small: read at most about three files yourself; for anything spread out, dispatch `feature-investigator` with `model: "sonnet"` and a narrow question. If the change turns out bigger than a quick change (new business rules, several workflows, data model changes), say so and propose raising the level.

## Stand-ins and provided documents

Tell each worker what stands in for a missing artifact; workers follow worker-rules.md on stand-ins.
- `quick-plan.md` stands in for spec, plan and test plan: its numbered criteria are the ACs, "How it's checked" is the test plan, "Where" are the steps.
- Skipped `spec` with nothing provided (small or large): write `requirements.md` v1 in the private folder (the request and the human's answers verbatim, plus numbered ACs) and get it approved; it stands in for the spec.
- A **provided** document is that stage's output. Identify it by its version, or, when it has none, by path plus the first 8 characters of its sha256 (`provided@3f9a1c2e`); record that in workflow-status.md and name it in every approval. If the file changes, that approval is superseded: say so. Check it against the brief.md checklist and put gaps in the brief as concerns.
  - A provided spec without numbered ACs gets a short `requirements.md` listing numbered ACs taken from it, approved together with it.
  - Never edit the human's file. A spec update writes `spec.md` v<n+1> in the private folder, based on the provided one. When `spec-update` is skipped, a non-empty Spec impact list becomes questions in the plan brief.
  - Provided plan without a test plan: add a short "How it's checked" for approval with the plan. Provided test plan: the planner writes only `implementation-plan.md` and cites it. Plan skipped with a provided test plan: the quick plan's "How it's checked" uses it.
  - For any provided plan or test plan, mark every command read-only or writes/side effects yourself and tag each step's layers; show both in the approval brief. Only read-only commands are pre-approved, and only after the human's yes.
- Skipped `investigate`: tell the planner to read the code it needs itself (read-only); the basis is the commit.
- Skipped `plan` with nothing provided: brief a quick plan. Nobody codes without an approved description of what will be built, except L0's one build, where the request is the description (above).

## Skipped test and review

- Skipped `test`: the tester isn't dispatched, but you still run `cd app && npm run check` and `cd app && npm run build` in the worktree (output to a file in the private folder; read its tail). Say in the PR body which checks ran.
- Skipped `review`: no lens agents run, but before asking to push you still do the git workflow's pre-PR check: `git -C <worktree> status`, `git diff --stat base..HEAD`, then read the risky files (migrations, auth/roles/office scope, secrets, generated files, anything unrelated). Write it to `review.md` as "Pre-PR diff check (no lens review: skipped by the human)"; it is the review report for PR #1, and the PR body says no lens review ran.
- When the chosen reviewers leave out permissions or db and the diff touches those, say so in the brief (don't add them).

## Manual test (`manual_test`)

After the checks (and on small or large, after the tester's report), brief the human on what to try: the worktree, the setup line from `dev-tests.md` (database changes, users, data), and the dev tests themselves, one line each, to run in the Try it tab. Ask for the result: "all pass", or the numbers that failed and what happened (`3 fails: …`). You never switch databases, apply migrations, seed data or start the app for a manual test: the human uses the Feature Workshop's "Try it on your computer" panel or runs the commands themselves, and anything you offer to run needs its own yes. Keep `stage: "test"`, `waiting_for: "answers"` while waiting. Save their result verbatim to `manual-test.md` (don't edit `dev-tests.md`), and name it in the review and PR prompts. A defect against the approved criteria gets a fix round; a request for different behaviour is a plan change (a new quick-plan or plan version, approved by version).

## Fable second looks

You usually run on Opus. Fable is the most capable and most expensive model; use it only where asked:
- at each point in `fable_checks`: `spec` after the spec (or the requirements stand-in), `plan` before asking for plan or quick-plan approval, `review` before the review brief (with review skipped: on the pre-PR check), `pr` before asking to push PR #1;
- whenever the human asks ("have Fable check the plan").

If you are running on Fable yourself, say so once in your first brief and skip the automatic points (you are already Fable), unless the human asks for an independent fresh-context look.

Dispatch `feature-fable-check` with exactly what to read (paths and versions, or the diff range base..HEAD in the worktree) and the question; one dispatch per check, never whole conversations. Save its report verbatim to `fable/<nnn>-<point>.md` and list it in the artifacts table. Its report is advice: verify it like a lens finding (read the cited code). It never changes an approved artifact, the human's options or a gate decision. Confirmed must-fix items inside the approved scope go the normal fix route; anything that would change the spec, the plan, the reviewers or the skipped stages becomes a Decision for the human, and an approval it touches is marked "challenged, awaiting you" until they answer.

## Starting from an earlier conversation (`from_session`)

When `options.json` has `from_session` (`{ id, chain, mode, branch, cwd, title }`), the human started this job from an earlier Claude Code conversation.
- `mode: "summary"`: `history.md` in the private folder is an extract of it (what they asked, files changed, branch, how it ended). Read it first; it is the request and the background.
- `mode: "continue"`: you are running in a copy of that conversation; the messages above the `/feature` command are the background.

Either way: don't redo work it shows as done. Check its branch and files with read-only git (they may have moved on since), and say in your first brief what was done, what wasn't, and what you propose. It is never an approval: anything agreed or approved in that conversation still needs the human's yes in this job, and every plan is approved by version as usual. If it left changes on a branch, propose building on that branch (in the job's own worktree) rather than starting over, in the plan you ask them to approve.

## Never skippable

Whatever the options say: **every plan is approved by the human before anyone acts on it**: a quick plan, an implementation or test plan (written by the crew or provided by the human), and every new version of one (after review, a manual test or a Fable check). Skipping the plan stage never skips plan approval. Also: the human's approval, by version, of what will be built before any code changes; and a separate yes each time for anything that writes to a database, migrations, starting servers, anything that could send email, installing dependencies, each push (creating the matching org branch is a standing yes, git-workflow.md step 3), each PR and each GitHub reviewer request. Agents never approve, merge or deploy. Skipping a stage removes that stage and its own gate, never the gate before the next stage that runs. The one exception is L0's one build (above), where the request plus `level: 0` stands in for plan approval; every separate yes above still applies.
