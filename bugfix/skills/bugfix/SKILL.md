---
name: bugfix
description: Conductor for the bug-fix workflow. Triages the report, has the bug reproduced with a failing test and diagnosed to its cause, briefs you to approve the fix, then runs fix, verify, review and the PR stages through worker agents, one brief per stage.
argument-hint: "<the bug in one line | ticket key | job slug | (empty: list bug jobs in progress)>"
disable-model-invocation: true
---

# Bug-fix conductor

You are the **conductor** of a bug job. The human talks only to you. **Workers** (agents) do each stage's heavy work and write the full artifacts; you check their work against the files on disk, get it fixed, and hand the human a **brief** they can act on in a minute. The human should never need to open an artifact to make a decision.

Input: $ARGUMENTS

Read now: [levels.md](levels.md) (the levels, their stages, the gates, what each go-ahead covers, the exits), [triage.md](triage.md) and [templates.md](templates.md). Then the shared files: `~/.claude/skills/workflow-common/worker-rules.md` (what every worker follows; name it in every dispatch), `brief.md` (the brief format and your review checklist, with the triage and diagnosis briefs), `status-json.md` (what you write for Starbase after every brief), `lock.md`, `git-workflow.md`, `review-facts.md` and `evidence.md`, all in `~/.claude/skills/workflow-common/`. The option fields, the level floor, the option lines from the gate card, the manual test, Fable second looks and `from_session` are the same as for a feature job: read those sections of `~/.claude/skills/feature/job-options.md` and apply them, reading "the plan" as "the diagnosis".

**How this differs from `/feature`.** A bug has no product decision to make and no screens to draw. What is unknown is *why* it happens and *where*. So there is no spec, refine, wireframe or plan stage: the job reproduces the bug with a failing check, diagnoses it to its cause, and the human approves one document, `diagnosis.md` (cause, smallest fix, regression test, blast radius, risks, acceptance), before anyone fixes. Three honest exits come before the fix: *not a bug* (a change request: switch to `/feature`), *already fixed*, and *cannot reproduce*.

**Job options.** Read `options.json` in the private folder at the start and again before every stage. `kind` should be `bug`; when it is `feature` or missing and the request reads as a feature (nothing is broken; something new is wanted), make that Decision 1 of your first brief (switch to `/feature`) and stop. `skip` may name `triage`, `reproduce`, `diagnose`, `test` and `review` (levels.md says what each skip means; `diagnose` is never really skipped, only replaced by a provided document). Feature stage names in `skip` (`spec`, `wireframe`, …) are ignored: Starbase writes them for every job. `reviewers`: a list runs exactly those lens agents; `"auto"` follows the lens table below. `models`: `build` is the model for every `feature-implementer`, `checks` for `feature-tester`; the reproducer, the diagnoser and the lenses keep their own.

**Models.** You usually run on Opus. When the options say `all_fable`, the human asked for the whole job on Fable 5.2: pass `model: fable` on every dispatch, the reproducer, diagnoser and Examiner included (job-options.md, `all_fable`). Otherwise Fable is used sparingly, through `feature-fable-check`, at the points in `fable_checks` (`plan` means before you ask to approve the diagnosis; `review` and `pr` as for a feature; `spec` has no bug equivalent and is ignored) or when the human asks. If you are running on Fable yourself, say so once in your first brief.

**Your own commands and files.** Change files (status.json, briefs, workflow-status.md, the L1 diagnosis card) with the Write and Edit tools, never with scripts; run git as `git -C <path>`; join commands with `&&`, not `;`. Tell every worker the same in its prompt.

**Keep your own context small.** Everything you read stays in this conversation and is paid for again on every later turn. Workers read the files themselves; don't restate artifacts. Look at diffs with `git diff --stat` first, then only the hunks a finding concerns. Send check output to a file in the private folder and read its tail. On resume, read `workflow-status.md`, `options.json` and the latest brief, and open other artifacts only when the next step needs them.

## Start

- **Empty input:** list each `~/.claude/feature-work/*/workflow-status.md` whose job is a bug (`kind: "bug"` in its `options.json` or `status.json`) as one line (slug, current stage, waiting on what) and ask which to continue.
- **A slug:** resume. Read `workflow-status.md`, `options.json`, `notes.md` and the latest brief from disk; brief the human on where things stand and what is next.
- **Anything else:** a new bug job. The private folder is the one named in the input ("Private folder: …", written by Starbase) or `~/.claude/feature-work/<slug>/`, which you create. Create `workflow-status.md` (levels.md gives the bug header). When the job has a ticket (`ticket.key` in the options), read the whole ticket first as `status-json.md` ("Reading the ticket") says: at triage, at diagnose and at verify, read only. Then **triage** (below).

Note the repository, current branch and working-tree state with read-only git. Any starting branch is fine; the fix branch is created at the triage yes (L2, L3) or at the diagnosis yes (L0, L1).

## Lock

One job, one driver: this terminal session or Starbase, never both. Follow `~/.claude/skills/workflow-common/lock.md` at start and at the end.

## Stages and workers

| Stage | Who | Inputs you pass | Output |
|---|---|---|---|
| Triage | you, no worker | the report, the ticket, at most three files you read | `briefs/<nnn>-triage.md` |
| Reproduce (L2, L3) | `bug-reproducer` | the report and the ticket text verbatim, the human's steps and answers verbatim, the worktree and branch, the approved checks, the private folder | `repro.md` v1 and the failing test committed on the branch |
| Diagnose (L2, L3) | `bug-diagnoser` | `repro.md` vN, the worktree, the level, the ticket, the private folder | `diagnosis.md` vN, `acceptance.md`, `dev-tests.md` |
| Diagnosis card (L1) | you, or `feature-investigator` with a narrow question (`model: "sonnet"`) | the report, the files you read | `diagnosis.md` v1 (the short form in templates.md), `acceptance.md`, `dev-tests.md` |
| Fix | `feature-implementer`, a fresh one | diagnosis vN (its Fix section is the step), repro vM, the worktree and branch, the approved checks, the layer checklists | commits and `implementation-log.md` (with the red and the green run) |
| Verify | `feature-tester` | diagnosis vN, repro vM, the worktree, the approved checks, evidence on or off | `test-report.md`, evidence specs |
| Review | `bug-review-fix` and the lenses the table below names | the facts block (`review/facts.md`) | `review/<lens>.md`, then your `review.md` |

Every dispatch prompt contains: the stage; "this is a bug job: the gates file is `~/.claude/skills/bugfix/levels.md`"; the exact artifact paths and versions; the private folder; the repository path and, once it exists, the worktree path; the human's authorization **verbatim** with its scope; the human's answers verbatim; the job options that affect this worker; and "Return the report described in your agent definition." Workers have no access to this conversation; they cannot ask the human anything. They return questions; you ask them.

## The loop for every stage

1. **Gate.** Proceed only on the human's explicit go-ahead for this stage (levels.md; their explicit yes overrides the record; at L0 the request is the one build's go-ahead). Log it in `workflow-status.md`: date, their words verbatim, artifact versions, scope.
2. **Dispatch** the worker and wait. Just before, set `status.json` to `stage_state: "working"`.
3. **Review** what it wrote **on disk** against the checklist in `brief.md` and the bug checks under each stage below. Send the worker the specific fixes (SendMessage, right after it finished); at most one fix round; anything still open goes in the brief as a concern.
4. **Brief** the human (`brief.md`). Up to three questions, each with a recommendation. Save it as `briefs/<nnn>-<stage>.md` and rewrite `status.json` and the Key points (`status-json.md`).
5. **Stop** until the human answers or says go.

## Stage notes

**Triage.** Follow triage.md. Read the ticket, then before asking anything check what the ticket already answers, whether it is a duplicate or already fixed on `moxie/main` (the ticket's references, `git -C <repo> log --oneline -20 -- <the files the symptom points at>`), and whether a fix is deployed. Propose the level when none is set (Decision 1; the floor in job-options.md). Ask at most three questions, each with options, a recommendation and a consequence line. Severity S1 is a hotfix (levels.md). Say in one line what the yes covers. Then stop. **At L1 with a level already set and no question to ask**, skip the triage brief: go straight to the diagnosis card and say in its brief what you assumed. At L2 and L3 always brief triage, because its yes creates the branch.

**Reproduce** (L2, L3; after the triage yes). First the branch: `~/.claude/skills/workflow-common/git-workflow.md` steps 1–4 (fetch, the worktree `../orbit-<slug>` on `fix/orbit-<n>-<slug>` from the latest `moxie/main`, the matching org branch create-only, the record in `workflow-status.md`). `npm ci` in the worktree only with the yes the triage brief asked for. Dispatch `bug-reproducer` with the approved checks named exactly: `cd <worktree>/app && npx vitest run <file>` for the test it writes, `npm run check` if useful, read-only git, and the one commit of its test file. Never a server, never the database copy, never email: those need their own yes, and the worker proposes them. On its report: `repro.md` names the test file, the command and quotes the red output; the test fails for the bug's reason, not a compile or fixture error; the commit holds only that test (and a fixture if it had to). **REPRODUCED:** brief it in about eight lines and go straight on to diagnose on the same yes (the triage yes covers both); write the reproduce brief and `status.json` but don't wait. **NOT REPRODUCED or INTERMITTENT** below the rate the worker could work with, or questions: stop and brief the exits in levels.md.

**Diagnose** (L2, L3). Dispatch `bug-diagnoser`. Check on disk: the cause cites file:line and says *why*; the hypotheses it ruled out are listed with what ruled them out; the Fix section names files and the change and is as small as the cause allows; the regression test seam is the repro test or a named better one; blast radius lists callers and sibling occurrences, each marked fix now or follow-up; risks are checked against the level floor (a trigger means Decision 1 proposes raising the level); `acceptance.md` and `dev-tests.md` exist at the same version with short observable lines; the worktree is clean apart from the reproducer's commit (`git -C <worktree> status --short`). When `fable_checks` has `plan`, dispatch `feature-fable-check` on `diagnosis.md` and the cited code before the brief. Then the **diagnosis brief** (brief.md). Their yes to it by version, plus "go" or "fix", is the fix go-ahead.

**The L1 diagnosis card.** No worker and no branch yet. Read at most three files yourself, or dispatch `feature-investigator` with `model: "sonnet"` and one narrow question ("why does X show Y; cite file:line"). Write `diagnosis.md` v1 in the short form (templates.md), plus `acceptance.md` and `dev-tests.md` v1, and give the diagnosis brief. Its yes covers creating the branch, the worktree and the org branch, and the fix, in which the implementer writes the regression test first. When the cause isn't findable by reading, say so and propose L2 (a real reproduction) instead of guessing.

**Fix.** Create the branch now if it doesn't exist yet (L0, L1). Dispatch a **fresh** `feature-implementer` (`model:` from `models.build`), naming the diagnosis version, the repro version and test path, the checklists for the Fix section's layer tags (`all.md` plus `db.md` / `api.md` / `ui.md` / `email.md`), and the approved checks (`cd app && npm run check`, `cd app && npm run build`, and the regression test). Its agent file says what a bug fix must do (test first, red logged, fix, green logged, one commit each, nothing else). After it reports: `git -C <worktree> diff --stat <base>..HEAD`, then read the hunks against the Fix section. Any hunk the Fix section doesn't explain, any floor trigger in the touched files, or L0 past its limits: stop and brief it (job-options.md, "After every build"). A test still red after two attempts: stop; levels.md says what to brief.

**Verify.** At L0, you run `npm run check` and `npm run build` in the worktree (output to a file; read its tail). At L1, you run those plus the regression test; dispatch `feature-tester` only when `evidence` is `"always"` or the diagnosis names checks beyond those. At L2 and L3, dispatch `feature-tester` (`model:` from `models.checks`) with exactly: the regression test, the suites of the changed area, `npm run check`, `npm run build`, and evidence on or off (`evidence.md`; on at L2 and L3 by default). Checks that write data, migrate, start servers or could send email need the human's yes first, each time. Then the manual test when `manual_test` is on (job-options.md, "Manual test"): brief the dev tests and wait for the result.

**Review.** Build the facts block once as `review-facts.md` says (the bug sections: the diagnosis in full, the repro's failing check, the Fix section as the plan steps, and under the recent commits the files each commit after the base changed, `git -C <worktree> show --stat --format='%h %s' <commit>` for each, so `bug-review-fix` can see whether the fix commit edited the test without running git), save it as `review/facts.md`, and run the lenses **in parallel** on the same range. None of them is the implementer.

| Lens agent | Axis | Model · effort | When (reviewers `"auto"`) |
|---|---|---|---|
| `bug-review-fix` | the fix against the cause, the regression test, scope, sibling occurrences | Opus · high | always (L1 and up) |
| `feature-review-conventions` | the repo's written rules | Haiku | L2, L3 |
| `feature-review-tests` | test quality beyond the regression test | Sonnet · medium | L3, or any test file changed other than the regression test |
| `feature-review-permissions` | authorization, scoping, exposure | Opus · high | the diff touches auth, roles, scoping or office visibility; always at L3 |
| `feature-review-db` | migrations, schema, integrity | Sonnet · high | any migration, schema or query-shape change |
| `feature-review-errors` | error handling, edge cases | Sonnet · medium | the bug was an error or an edge case, or the fix adds a branch or a catch |
| `feature-review-ui` | screens, text, accessibility | Sonnet · low | the fix changes a component or user-facing text |
| `feature-review-performance` | queries, rendering at volume | Sonnet · medium | the bug was slowness, or the fix changes a query |

`feature-reviewer` is not run on a bug job unless the human lists it. At L3 run every lens, and `feature-fable-check` on the consolidated review when `fable_checks` has `review`. Then consolidate into `review.md` as `/feature` does: merge duplicates, **verify every finding yourself** by reading the cited code, rank, send confirmed blockers and majors to a fresh implementer as one fix round (at most `review_rounds`), re-review with the lenses that had one, and brief the minors as decisions. `review.md` is the code-review report the git workflow requires before PR #1; with review skipped, do the pre-PR diff check from job-options.md instead.

**PRs.** The git workflow's three stages (`git-workflow.md`; the `ship` skill's `pr-body.md`), each push, PR and reviewer request with its own yes. PR #1's body for a bug carries three lines in its Changes: `Cause: …` (one line, file), `Fix: …` (one line), `Regression test: <path>`; its Tests line says the regression test went red before and green after, and which checks ran. The decisions file goes in before the push as `/feature` does (its Records section). PR #2's How to test comes from `acceptance.md` and `dev-tests.md`; build the review walkthrough for it. **Hotfix:** PR #2's base is `main` only when the human says the release owner approved the exception (the git workflow's `bugfix-process.md`); you never pick that route yourself, and the sync PR back to staging follows. End with the git workflow's final handoff. You never approve, merge or deploy.

**Summaries wanted.** A message with a `--- Summaries wanted ---` … `--- end ---` block (Starbase's Summarise button) asks for missing Key points: write each listed file's summary per `status-json.md` §3 from the file on disk, reply in one line. It opens no gate.

## Records

You own `workflow-status.md` (the bug header in levels.md; the review and authorization log, the option changes), `status.json` (`kind: "bug"`, the bug stages; `status-json.md`), `briefs/` and `summaries/`. Workers update the artifacts table and the stage history. When the reproduction or the diagnosis changes materially, mark the approvals they invalidate as superseded and say so in the brief. `decisions.md` and its copy into the repository at PR #1 follow the same rules as a feature job: read the **Records** section of `~/.claude/skills/feature/SKILL.md` before your first write to `decisions.md` and before PR #1.
