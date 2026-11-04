# Workflow skills

Skills and worker agents for [Claude Code](https://claude.com/claude-code) that take a feature or a bug from a one-line request to reviewed pull requests, with a human sign-off at every stage.

You talk to one conductor: the **Foreman** (`/feature`) for a feature, or `/bugfix` for a bug. It hands each stage to a worker agent, checks the result against the files on disk, and gives you a short brief to approve before anything moves on. The [Starbase](https://github.com/vigneshrs-moxie/feature-workshop) shows these jobs in a browser; it needs this workflow installed.

## Install

You need Claude Code installed and logged in (`claude` works in your terminal).

```sh
git clone https://github.com/vigneshrs-moxie/workflow-skills.git
cd workflow-skills
./install.sh
```

The script does three things:
- Links every skill folder under `common/`, `feature/`, `bugfix/` and `tools/` into `~/.claude/skills/`, and every agent file into `~/.claude/agents/`. Because they are links, `git pull` here updates them in place.
- Moves anything already there with the same name to `~/.claude/backups/claude-feature-workflow/<date>/`, outside the skills folder so Claude Code doesn't load it twice.
- Clones the [git workflow docs](https://github.com/vigneshrs-moxie/moxie-portal-git-workflow) to `~/Projects/moxie-portal-git-workflow`, or updates them if already cloned. The conductors read them before any branch or PR step. Keep that location; the skills look for it there.

Run it again after every `git pull`. Set `CLAUDE_DIR` to install somewhere other than `~/.claude`. Windows: `powershell -ExecutionPolicy Bypass -File install.ps1`.

Then in Claude Code, inside the repository you work on:

```
/feature Add a "Download CSV" button to the invoices page
/bugfix The Warnings pop-up cuts long reasons off after one line
```

## What is in here

The repository is split by who uses what. Each group's `skills/*` and `agents/*.md` are linked into `~/.claude`.

| Folder | What | Installed as |
|---|---|---|
| `common/` | What both workflows share: the worker rules, the git workflow summary, the `status.json` contract, the brief format, the job lock, the review lens rules and the facts block, evidence, the layer checklists; and the shared agents (the implementer, the tester, the review lenses, the Fable check). | `~/.claude/skills/workflow-common`, `~/.claude/agents/feature-*` |
| `feature/` | The feature workflow: the `/feature` Foreman and its stage skills, and the writers only a feature needs. | `~/.claude/skills/feature*`, `~/.claude/agents/feature-spec-writer.md`, `feature-wireframer.md`, `feature-investigator.md`, `feature-planner.md` |
| `bugfix/` | The bug-fix workflow: the `/bugfix` conductor and the three bug agents. | `~/.claude/skills/bugfix`, `~/.claude/agents/bug-*` |
| `tools/` | Standalone skills either workflow or a person uses: `wireframe`, `ship`, `review-walkthrough`, `uat-guide`. | `~/.claude/skills/<name>` |
| `docs/design/` | Design notes, including why a bug job is shaped differently from a feature job. | not installed |

The shared agents keep their `feature-` names (`feature-implementer`, `feature-tester`, `feature-reviewer`, `feature-review-*`, `feature-fable-check`); both conductors dispatch them.

### Skills

| Skill | What it does |
|---|---|
| `feature` | The Foreman. Runs clarify → spec → screens → investigate → plan → build → test → review → PRs through the agents below, one brief per stage. Holds the job options (how much process a job gets), the levels, and stacks. |
| `bugfix` | The bug-fix conductor. Runs triage → reproduce → diagnose → fix → verify → review → PRs. A bug has no spec or plan: the human approves one document, the diagnosis (cause, smallest fix, regression test, blast radius, risks), before anyone fixes. Holds `levels.md` (bug levels, gates, exits), `triage.md` and `templates.md`. |
| `workflow-common` | Not a command. The rules and formats both conductors and every worker read: `worker-rules.md`, `git-workflow.md`, `status-json.md`, `brief.md`, `lock.md`, `review-lens-rules.md`, `review-facts.md`, `evidence.md`, `checklists/`. |
| `feature-spec` | Drafts a product spec from a request and recommends the small or large route. Holds `workflow-gates.md`, the rules for what each feature stage needs before it may start. |
| `feature-refine` | The detailed product interview for a large feature, one question at a time. |
| `feature-investigate` | Read-only look at how the repository behaves today, written up as private findings. |
| `feature-plan` | The implementation plan and test plan, from the spec and findings; also the `acceptance.md` and `dev-tests.md` templates both workflows use. |
| `wireframe` | Draws the screens for a feature or product idea and publishes them as a private review page before anything is built. Four fidelities (text, sketch, lo-fi, hi-fi in the app's own design), states as tabs, Before/Now pairs, clickable exits, two options side by side wherever there is a real choice; reviewers mark, pick and annotate on the page; it writes a build brief and keeps a gallery. |
| `feature-wireframe` | The Screens stage of a `/feature` job: runs `wireframe` in job mode for the Foreman and Starbase. |
| `ship` | Moves a finished branch through the three PR stages from the terminal: fork branch → same-named org branch (PR #1), org branch → staging (PR #2, Raj reviews), staging → main (PR #3), the sync route when PR #2 conflicts with staging, review rounds, and the hotfix route. `preflight.py` is read-only. It opens a PR only when you say so and never merges, approves or pushes to staging or main. |
| `review-walkthrough` | A one-page cue sheet for an in-person review of a branch or PR, in four zoom levels. |
| `uat-guide` | A one-to-two page UAT guide for non-technical stakeholders, as a Claude Docs doc and a Letter PDF. |

### Agents

Each file sets a worker's model, effort and tools. The conductors dispatch them; you never call them directly.

- **Shared** (`common/agents/`): `feature-implementer` (builds a plan step, or a bug fix: regression test first, red, fix, green), `feature-tester`, the review lenses `feature-reviewer` (spec conformance), `feature-review-permissions`, `-db`, `-tests`, `-ui`, `-errors`, `-performance`, `-conventions`, and `feature-fable-check` (a short, independent second look on request).
- **Feature only** (`feature/agents/`): `feature-spec-writer`, `feature-wireframer`, `feature-investigator`, `feature-planner`.
- **Bug only** (`bugfix/agents/`): `bug-reproducer` (a failing test that goes red on the exact symptom, committed on the fix branch; "cannot reproduce" is a valid result), `bug-diagnoser` (ranked hypotheses, one confirmed root cause, blast radius and sibling occurrences, the smallest fix, the regression seam, risks, acceptance), `bug-review-fix` (the review lens that checks the fix against the cause, the regression test, scope and siblings).

## How a feature job runs

1. **Clarify.** For a standard or large job, the Foreman first asks up to five questions that would change what gets built, each with options, a recommendation and what each option means. Often there are none.
2. **Spec.** The Foreman drafts a spec from your request and answers, and asks at most three questions.
3. **Level.** Each job gets a level of process, L0 (a tweak) to L3 (large or risky). The Foreman suggests one from the request and the code it touches; you confirm or change it. Risky changes (migrations, auth, scoping, email) always get more review.
4. **Screens.** When the spec names a page, dialog, sheet or email, the screens are drawn for review before any code; what you pick goes into the spec.
5. **Investigate and plan.** Read-only findings, then a plan you approve before any code is written.
6. **Build.** A fresh implementer per plan step, one local commit per step, in its own git worktree.
7. **Test and review.** The test plan runs; review lenses report; fixes get one round by default.
8. **PRs.** Pushed to your fork only. Pull requests to the organisation repository are opened only when you say so.

## How a bug job runs

A bug is a different job from a feature: what to build is known, what is unknown is *why* it happens and *where*. So the stages are different, the levels mean something different, and the review asks different questions. The reasoning is in [docs/design/2026-11-04-bugfix-workflow.md](docs/design/2026-11-04-bugfix-workflow.md).

1. **Triage.** The conductor reads the ticket and the code the symptom points at, checks whether it is a duplicate, already fixed or not a bug at all (then it proposes `/feature`), proposes the level and names the severity, and asks at most three questions, only ones that change how the bug is reproduced or fixed. Its yes creates the `fix/` branch.
2. **Reproduce** (L2 and up). A worker writes a test that goes red on the exact symptom, tightens it, and commits it on the fix branch. "Cannot reproduce" is a reported outcome with what was tried, never a guess.
3. **Diagnose.** A worker traces the symptom to one confirmed root cause through ranked hypotheses, lists the blast radius and every sibling occurrence of the same mistake, and proposes the smallest fix, the regression test and the risks. At L1 the conductor writes this as a short card from reading the code. **You approve the diagnosis**; that is the only approval before the fix.
4. **Fix.** One implementer: the regression test runs red (or is written first and run red), the fix is made, the test runs green, both runs are logged; one commit each; nothing beyond the diagnosis's Fix section.
5. **Verify.** The tester proves the regression test and the related suites pass, runs the checks, and records evidence for each acceptance line a person can see. Then you try it by hand.
6. **Review.** `bug-review-fix` always, plus the risk lenses the diff calls for. Findings go through one fix round by default.
7. **PRs.** As for a feature. A hotfix takes the git workflow's direct-to-main exception only on the release owner's word.

| Level | What runs |
|---|---|
| L0 Tweak (hotfix) | one build (test first, then the fix), checks, you look at the diff |
| L1 Small | triage → diagnosis card → fix → checks → you try it → `bug-review-fix` |
| L2 Standard | triage → reproduce → diagnose → fix → verify with evidence → you try it → the bug lens plus what the diff touches |
| L3 Risky | L2, every lens, and a Fable second look at the diagnosis and the review |

Every job keeps its own private folder under `~/.claude/feature-work/<slug>/` with its documents, briefs and a `status.json` Starbase reads. Nothing from that folder is committed to the repository you are working on, except the job's decisions file at PR #1.

## Adapting it

- `common/skills/workflow-common/git-workflow.md` and `feature/skills/feature-spec/workflow-gates.md` describe one team's remotes, branch naming and PR stages. Edit them for yours.
- `common/skills/workflow-common/checklists/` holds the review checklists per area (API, database, email, UI). Add your own.
- Model choices live in each agent's front matter; a job's options can set the build and test models per job.
- The level floor (which paths force a higher level) lives in `feature/skills/feature/job-options.md` and in Starbase's `level-rules.js`; change both together.

## Credits and license

The bug-fix workflow's reproduce-first loop, root-cause-before-fix rule and three-failed-fixes stop draw on [Superpowers](https://github.com/obra/superpowers) by Jesse Vincent (MIT) and on Matt Pocock's `diagnosing-bugs` skill, rewritten in this workflow's own words. Planned changes for test-first building and checking before claiming done draw on Superpowers too.

MIT licensed. See [LICENSE](LICENSE).
