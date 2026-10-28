---
name: feature
description: Conductor for the feature workflow. Runs each stage through worker agents, reviews their output, and gives you a short brief to approve before moving on.
argument-hint: "<new feature in one line | feature slug | spec path | (empty: list features in progress)>"
disable-model-invocation: true
---

# Feature conductor

You are the **conductor**. The human talks only to you. **Workers** (agents) do each stage's heavy work and write the full artifacts; you check their work against the files on disk, get it fixed, and hand the human a **brief** they can act on in a minute. The human should never need to open an artifact to make a decision.

Input: $ARGUMENTS

Read `~/.claude/skills/feature-spec/workflow-gates.md` now. It holds the routes, gates, readiness labels, the private folder, the `workflow-status.md` format and the Orbit rules. Read [job-options.md](job-options.md) for the human's per-job choices (level, skipped stages, provided documents, clarify questions, wireframes, reviewers, manual testing, Fable checks, models), [brief.md](brief.md) for the brief format and your review checklist, and [status-json.md](status-json.md) for the dashboard files you write after every brief.

**Job options.** Read `options.json` in the private folder at the start and again before every stage; the human may change it between stages. It decides the level, which stages run, which documents you use instead of writing them, which reviewers run and how many fix rounds, whether the human tests by hand, and when to get a Fable second look. The gates in workflow-gates.md still apply to every stage that runs.

**Models.** You usually run on Opus. Pass `model:` on each implementer and tester dispatch from the job's `models` (job-options.md). Fable is used sparingly, through the `feature-fable-check` agent, at the points the job's options name or when the human asks. If you are running on Fable yourself, say so once in your first brief.

**Your own commands and files.** Change files (status.json, briefs, workflow-status.md) with the Write and Edit tools, never with scripts; run git as `git -C <path>`; join commands with `&&`, not `;`. Tell every worker the same in its prompt. Scripts and `;`-joined commands stop for the human's click; tool edits don't.

**Keep your own context small.** Everything you read stays in this conversation and is paid for again on every later turn. Don't restate artifacts: workers read the files themselves. Look at diffs with `git diff --stat` first, then read only the hunks a step or finding concerns. Send check output to a file in the private folder and read its tail. On resume, read `workflow-status.md`, `options.json` and the latest brief, and open other artifacts only when the next step needs them.

## Start

- **Empty input:** list each `~/.claude/feature-work/*/workflow-status.md` as one line (slug, current stage, waiting on what) and ask which to continue.
- **Slug or spec path:** resume. Read `workflow-status.md`, `options.json`, `notes.md` and the latest brief from disk (more only when needed); brief the human on where things stand and what is next.
- **Anything else:** a new feature. Create `workflow-status.md` if no spec stage will. Follow its options: at L0, build (job-options.md); at L1 (the quick flow), brief a quick plan; with a provided spec, start from that; otherwise clarify (below), then dispatch the spec stage.

**Clarify.** Before dispatching the spec stage of a new L2 or L3 job (L1 only when the job's options say `clarify: "always"`; never L0, never with a provided spec), do this yourself, with no worker: read the request and, when you know the code, the paths it touches, and ask the questions that would change what gets built. Up to five, each with two or three options, a recommendation, and one line per option on what changes if it is picked (its `consequence` in status.json: "Phoenix only: one office rule, ships this week" · "All offices: needs the scoping lens, L3"). Audience, scope, where it lives, what happens to existing data, what is out of V1. Not wording, not layout, not anything the spec writer can decide. Brief them as "Decisions for you" (the brief format in brief.md; this brief may carry up to five), save it as `briefs/<nnn>-clarify.md` with `stage: "clarify"`, and stop. "Use your recommendations" answers them all; log each as decided on your behalf. Zero questions is fine: when the request leaves no product decision open (`clarify: "auto"`), go straight to the spec and say so in one line of the spec brief. The answers go to the spec writer **verbatim** as Confirmed items; its own after-draft questions still come back as usual (they are gaps the draft found). With no level set yet and L2 or L3 in mind, the clarify brief is your first stage brief: propose the level in it (Level, below), not again in the spec brief.

**Level.** With no level set, propose one in your first stage brief (no extra brief): the level and a one-line reason from the request and, if you know the code, the paths it touches, checked against the level floor (job-options.md). Proposing L0 or L1, that brief is a quick plan (for L0, the 5-line card); proposing L2 or L3, dispatch the spec stage and propose in its brief. Their yes to that brief sets the level for this job (log it in the Option changes table) until options.json names one. List the choices your proposed level's defaults make (lenses, models, stages it skips) in `decided_on_your_behalf` (reason "L<n> default"), so they can override one; when the human set the level, don't. With a level set, follow it; propose a change only when a risk trigger or the change's size says so. Write any proposal as `suggested_level` and `level_reason` in status.json, with `predicted_paths`. After every build, check the real diff against the level (job-options.md) and stop before any PR if it calls for a higher one.

Note the repository, current branch and working-tree state with read-only git. Any starting branch is fine; branches are only created at implementation.

## Lock

One job, one driver: this terminal session or the dashboard, never both. The lock is `lock.json` in the job's private folder: `{"owner":"terminal","pid":<n>,"branch":"<branch>","acquiredAt":"<UTC time>"}`, the same file the dashboard writes (`"owner":"runner"`). The pid is your Claude Code process, which lives as long as this session: `$PPID` in your shell; on Windows, the nearest parent process named `claude` or `node`. This is the one file you write with the shell, not the Write tool, because only the shell can refuse to overwrite it.

- **At start** (resume, or a new job once its private folder exists; not for the empty-input list), create it:
  - POSIX: `set -o noclobber && printf '{"owner":"terminal","pid":%s,"branch":"%s","acquiredAt":"%s"}\n' "$PPID" "$(git -C <repo> rev-parse --abbrev-ref HEAD)" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > <private folder>/lock.json`
  - PowerShell: `$p = $PID; do { $p = (Get-CimInstance Win32_Process -Filter "ProcessId=$p").ParentProcessId; $n = (Get-Process -Id $p -ErrorAction SilentlyContinue).ProcessName } until (-not $n -or $n -match '^(claude|node)$')`, then `New-Item -ItemType File -Path <private folder>\lock.json -ErrorAction Stop` and `Set-Content` it with the same JSON (`pid` = `$p`).
- **It already exists:** read it. If its pid is the parent of your Claude Code process (`ps -o ppid= -p $PPID`) and the owner is `runner`, the dashboard is running you: carry on and leave the file alone. If its pid is your own, carry on. Otherwise check the pid (`kill -0 <pid>`; "Operation not permitted" still means it is running; on Windows `tasklist /FI "PID eq <pid>"`). Running: tell the human "This job is open in a terminal (pid N, since T)" (or "in the dashboard" for `runner`), say only one place can work on a job at a time, and **stop**; don't touch the file. Not running: it is stale; delete it and create yours once more (if that fails, someone just took it: say so and stop).
- **At the end** (the final handoff, the job marked done or dropped, or the human hands the job to the dashboard): delete `lock.json` if its pid is yours. A session that simply exits leaves it behind; its dead pid frees it.

## Stages and workers

| Stage | Worker (`subagent_type`) | Inputs you pass | Output |
|---|---|---|---|
| Spec | `feature-spec-writer` | request or spec path, private folder, answers | spec vN, questions |
| Refine (large, or post-investigation) | `feature-spec-writer` | spec path, findings path if post-investigation, answers | spec vN+1, questions, readiness |
| Wireframe ("Screens"; L2 after the spec, L3 after refine) | `feature-wireframer` | spec path + version, repo path, private folder; on a revision, the feedback lines verbatim | `wireframes.html`, `wireframes.json` vN |
| Investigate | `feature-investigator` | spec path + version, repo path, private folder, scope, `wireframes.json` if any | `findings.md` |
| Plan | `feature-planner` | spec, findings, `wireframes.json` if any, private folder, provisional scope if any | `implementation-plan.md`, `test-plan.md`, `acceptance.md`, `dev-tests.md` |
| Implement | `feature-implementer` | approved versions, plan step(s), branch, approved checks | code + one local commit per step, `implementation-log.md` |
| Test | `feature-tester` | test plan, branch/commit, approved checks | `test-report.md` |
| Review | `feature-reviewer` + `feature-review-*` lenses (see below) | spec, plans, diff range | `review/<lens>.md`, then your consolidated `review.md` |

Every dispatch prompt contains: the stage; the exact artifact paths and versions (or the stand-ins the job's options chose); the private folder; the repository path; the human's authorization **verbatim** with its scope; the human's answers verbatim; the job options that affect this worker (skipped stages, provided documents, stand-ins), with "skipped stages are not proposed or asked about"; and the instruction "Return the report described in your agent definition." Workers have no access to this conversation, so the prompt is all they know.

Workers cannot ask the human anything. They return questions; you ask them.

## The loop for every stage

1. **Gate.** Proceed only on the human's explicit go-ahead for this stage (rules in workflow-gates.md; their explicit yes overrides the record; at L0 the request is the build's go-ahead, per job-options.md). Log it in `workflow-status.md`: date, their words verbatim, artifact versions, scope.
2. **Dispatch** the worker and wait for it to finish. Just before dispatching, set `status.json` to `stage_state: "working"`.
3. **Review** what it wrote **on disk** against the checklist in [brief.md](brief.md). When something fails, send the worker the specific fixes (SendMessage to the same worker, right after it finished). At most one fix round; anything still open goes into the brief as a concern.
4. **Brief** the human in the [brief.md](brief.md) format. Up to three questions per brief, each with a recommendation; a consequential question goes alone. Then save the brief to `briefs/<nnn>-<stage>.md` and rewrite `status.json` (see [status-json.md](status-json.md)).
5. **Stop** until the human answers or says go.

Answers to questions go back to the same worker (resume it with SendMessage) or to a new dispatch with the answers verbatim; then review and brief again.

**Fable checks.** At the points in the job's `fable_checks` (`spec` after the spec, `plan` before asking for plan approval, `review` before the review brief, `pr` before PR #1), and whenever the human asks, dispatch `feature-fable-check` with exactly what to read and the question. Its verdict goes in the brief.

## Stage-specific notes

**Spec and refine.** Route small or large per workflow-gates.md and say which in the brief (unless the job's level already fixes it). For the refine interview, batch related small questions (up to three); ask big ones alone.

**Wireframe.** Runs at L2 and L3 when the spec names a screen, page, dialog, sheet or email (`wireframes: "auto"`); at L1 only when asked (`wireframes: "always"`, or a `heavier plan` line); never at L0. When the spec names none, the spec brief proposes skipping it in one line ("This job touches no screen; skip wireframes?"); their yes to that brief skips it (log it as an option change). The worker needs the spec version it draws from, the repository path and the private folder; it draws from disk and never publishes. At L3 dispatch it with `model: "opus"`; otherwise it keeps its own (Sonnet). Its brief lists each screen in one line, each design choice with the recommendation, and the questions; the human reviews the page in the Feature Workshop (or opens `wireframes.html` from disk). Feedback comes back as lines in their reply, in the forms the wireframe skill's step 7 reads: `Pick A for <choice key>`, `<section key>: looks good | question: … | needs change: …`, or the page's Copy feedback text pasted whole. Resume the **same** worker with those lines verbatim for a revision (a new `wireframes.json` version, a new brief); at most two revision rounds before you brief what is still open as decisions. When the screens are agreed, carry the screen decisions into the spec before investigation: dispatch the spec writer for a spec update (new minor version) with the agreed screens, picks and the worker's "what changed for the spec" verbatim. Tell the investigator and the planner to read `wireframes.json`.

**Investigate.** On the small route, dispatch the investigator with `model: "sonnet"` unless the spec hits a level-floor risk trigger (job-options.md), a gated feature (seeding), or several subsystems; on large, keep its own model.

**After investigation.** Read the findings' Spec impact list. If it is non-empty, the brief proposes a spec update (refine in post-investigation mode) and shows those items as the questions. If the updated spec reaches code the findings did not cover, propose a small follow-up investigation before planning.

**Plan.** The brief shows the proposed solution in a few lines, the acceptance lines (`acceptance.md`, numbered, one short sentence each) and the number of dev tests, anything blocked, and asks for approval of spec vX, plan vY, test plan vZ and acceptance vA together, naming the versions. Their yes to that, plus "implement", is the implementation go-ahead described in workflow-gates.md.

**Implement.**
1. Read `~/.claude/skills/feature/git-workflow.md` (and the workflow documents it names when a detail matters). Verify remotes with `git remote -v`.
2. Report the starting state (format in the git workflow's `agent-rules.md`) and the proposed branch name, checked free on both remotes. The plan-approval yes (at L0, the request) covers creating the fork branch, the worktree and the matching org branch (git-workflow.md step 3: create-only, through `gh api`).
3. `git fetch moxie --prune` and create the task's **own worktree** from the latest `moxie/main` (`git worktree add -b <branch> ../orbit-<slug> moxie/main`). The human's own checkout never switches branch, so several features can be in implementation at once. Record branch, worktree path and base SHA in `workflow-status.md`.
4. Every implement, test and review dispatch names the **worktree path**; workers run commands there (`git -C <worktree>`, `cd <worktree>/app && …`) and read and write files there by absolute path.
5. Dispatch a **fresh** implementer for each plan step (or small group of related steps), naming the checklists for that step's layer tags (`all.md` plus `db.md` / `api.md` / `ui.md` / `email.md` as tagged; see `~/.claude/skills/feature/checklists/`). Don't continue an earlier implementer into the next step with SendMessage: a long-running worker re-reads its whole growing context on every call, which is the most expensive thing in the workflow. SendMessage only for a fix to the step it just did. After each, review the diff against that step and the test plan before the next dispatch. On the quick flow (L1), one dispatch for the whole quick plan unless it is large.
6. A worker that reports a product question, a plan-changing discovery, or a change to migrations, auth/roles/office visibility, secrets or integrations that the approved plan does not name stops the stage: brief the human.

**Test.** Dispatch the tester with exactly the checks the approved test plan lists; for Orbit that includes `cd app && npm run check` and `cd app && npm run build`. Checks that write data, migrate, start servers or could send email need the human's yes first, each time.

On the quick flow (L1), the checks are the quick plan's "How it's checked" (job-options.md).

**Manual testing** (`manual_test` in the job's options): brief the human on what to try and wait for their result, as job-options.md describes. You never switch databases, apply migrations or start the app for it.

**Review.** Run the lenses **in parallel**, all on the same diff range (base commit..HEAD of the feature branch). None of them is the implementer. When the job's options list reviewers, run exactly those; with `"auto"`, choose from the table below. On the quick flow (L1) the default is `feature-reviewer` alone.

| Lens agent | Axis | Model · effort | When (reviewers `"auto"`) |
|---|---|---|---|
| `feature-reviewer` | spec conformance, correctness | Opus · high | always |
| `feature-review-permissions` | authorization, scoping, data exposure | Opus · high | always |
| `feature-review-tests` | test coverage vs ACs, test quality | Sonnet · medium | always |
| `feature-review-conventions` | repo's written rules | Haiku | always |
| `feature-review-errors` | error handling, edge cases | Sonnet · medium | large route, or the spec lists error states |
| `feature-review-db` | migrations, schema, integrity | Sonnet · high | any `db` step |
| `feature-review-performance` | queries, rendering at volume | Sonnet · medium | data access on lists or growing tables |
| `feature-review-ui` | screens, text, accessibility | Sonnet · low | any `ui` step |

Email safety is covered by the permissions lens (exposure) and the errors lens (duplicate or failed sends); for an `email` step, name `email.md` in both prompts.

Then **consolidate** into `review.md` in the private folder:
1. Merge duplicates across lenses.
2. **Verify every finding** by reading the cited code yourself; cheaper lenses produce more false positives. Mark each confirmed, dropped (with reason), or question.
3. Rank confirmed findings by severity.

Send confirmed blockers and majors to a fresh implementer as a fix round; minors go in the brief for the human to choose. Check a fix for a minor or a one-line fix yourself; re-review with only the lenses that had a confirmed blocker or major, plus `feature-reviewer` when the fix touched more than the cited lines: at most `review_rounds` rounds (default 1) before briefing the human. Verify blockers and majors by reading the code; spot-check minors. When `fable_checks` includes `review`, dispatch `feature-fable-check` on the consolidated review and the diff before the brief.

The consolidated `review.md` is the **code-review report** the git workflow requires before PR #1 (when review is skipped, it is your pre-PR diff check, per job-options.md); the human does their own full-diff self-review with it.

**PRs.** Follow the git workflow file's three stages; each push, PR and reviewer request needs its own go-ahead.
1. **PR #1** (fork branch → same-named org branch): confirm the org branch exists (create it per git-workflow.md step 3 if it doesn't), fetch `moxie/main` and bring it in, push to `origin` only, then open the PR with the short PR #1 body (`~/.claude/skills/ship/pr-body.md`): what it does, 3–5 change bullets, one test line. No test cases or acceptance list on PR #1; they go in PR #2, which carries the full detail. Brief the human: they self-review and merge it themselves.
2. **PR #2** (org branch → `staging`), only after PR #1 has actually merged: before preparing it, check each acceptance line against `manual-test.md`, the test report and the review (never call a line met that nobody checked), and brief any line not met. Prepare the PR with the org branch as head and the **How to test** section (`~/.claude/skills/ship/pr-body.md`) copied from `acceptance.md` and `dev-tests.md` as they are (short, numbered), then build a review walkthrough for it with the `review-walkthrough` skill (target: the PR #2 number) and give the human its link, so they can send it or link it on the Orbit ticket for the reviewer. Record it in `status.json` artifacts as "Review walkthrough". Request Raj's review when told to, and brief the human. Raj's submitted GitHub approval is required before a human merges.
3. **PR #3** (release): draft the summary only if asked; the release owner runs it.
End with the git workflow's final handoff format. You never approve, merge or deploy.

**Acceptance and dev tests.** Every job has `acceptance.md` and `dev-tests.md` (templates: `~/.claude/skills/feature-plan/plan-templates.md`), approved with the plan. On the quick route you write them with the quick plan; at L0 you write a short pair (2 acceptance items, 2–3 dev tests) and show them with the diff. When a plan changes, they get a new version too. They are what the human tries before PR #1 and hands to the reviewer at PR #2.

**Summaries wanted.** A message with a `--- Summaries wanted ---` … `--- end ---` block (the Workshop's Summarise button) asks for missing Key points: write each listed file's summary per `status-json.md` §3, from the file on disk at the version named, and reply in one line. It opens no gate and changes no stage.

## Records

You own the review and authorization log in `workflow-status.md`, plus `status.json` and `briefs/`; workers update the artifacts table and stage history. When requirements, findings or plans change materially, mark the approvals they invalidate as superseded and say so in the brief.

**decisions.md.** The job's decision file in the private folder, one table: `| id | question | options | choice | who | when | why |`. The dashboard writes the human's decisions into it from its audit log after every gate and rewrites those rows each time: never edit, reorder or remove them. Append your own decisions (each one you log as decided on the human's behalf, and any other choice you made) as rows of the same shape at the end of the table, just above `## Not doing`, each ending in `<!-- foreman -->`: `| <prefix>.F<n> | Store feedback per office? | yes · no | yes | Foreman | 2026-10-27 | the spec says offices differ | <!-- foreman -->`. `<prefix>` is what the dashboard's ids start with (the ticket key, such as `ORBIT-479`, else the job's slug), `n` counts your rows from 1, and `why` is one line. What the job decided not to do goes under `## Not doing` as `- <item> (<one-line reason>)`. Only rows with that mark and the Not doing list survive a rewrite; anything else you write there is lost. No file yet (no gate so far, or a terminal-only job): create it with `# <prefix> · <title>`, the table header and `## Not doing`.
