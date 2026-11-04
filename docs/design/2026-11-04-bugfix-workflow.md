# The bug-fix workflow: design

Date: 2026-11-04 · Status: built on `feature/bugfix-workflow`, not merged · Author: the Foreman's maintainers, with Claude

The feature workflow (`/feature`) turns a one-line request into reviewed pull requests through spec → screens → investigate → plan → build → test → review → ship. It is the wrong shape for a bug: a bug has no product decision to make and no screens to draw, but it has a question the feature workflow never asks, *why does this happen?* This document says how a bug job differs, what the quickest responsible process is, what was borrowed from outside, and how it is laid out in this repository and picked up by Starbase.

## 1. A feature and a bug are different jobs

| | Feature | Bug |
|---|---|---|
| What is unknown | **What** to build. The product decisions. | **Why** it happens and **where**. The behaviour wanted is already known (it worked, or the ticket says what should happen). |
| First evidence | A spec the human agrees with. | A reproduction: a failing check that goes red on this exact symptom. |
| The document the human approves before code | Spec + plan + test plan, by version. | One diagnosis: cause, smallest fix, regression test, blast radius, risks. |
| Stage that creates value | Plan (the design of the change). | Diagnose (the root cause). A fix without it is a symptom patch. |
| Screens | Drawn before any code when the spec names one. | Never drawn; the UI already exists. |
| Investigation | Broad: how the repository behaves today around every requirement. | Narrow: trace one code path from the symptom back to its source. |
| Build | Fresh implementer per plan step, one commit each. | One commit for the regression test (red), one for the fix (green). No "while I'm here". |
| Test | The test plan's checks against acceptance criteria. | The regression test proves red → green; the related suites prove nothing else broke. |
| Review axes | Spec conformance plus seven lenses. | Does the fix match the cause, not the symptom? Would the test catch the bug? Is the diff only the fix? Is the same mistake elsewhere? Plus risk lenses only when the diff touches their area. |
| Outcomes | Built, or scoped down. | Fixed, **cannot reproduce**, **not a bug** (a change request: switch to `/feature`), or **already fixed** on main. |
| Git | `feature/orbit-<n>-<slug>`; PR #2 to staging. | `fix/orbit-<n>-<slug>`; PR #2 to staging, or to `main` for a hotfix the release owner approves (`bugfix-process.md`). |
| Timing | Scheduled. | Has a severity. A hotfix compresses the briefs, never the stages. |

Two things stay the same on purpose: the levels (L0–L3, the same risk floors and the same option fields, so Starbase's level picker, auto-level and options editor work unchanged) and the shipping stages (PR #1, PR #2, staging QA, PR #3 through the `ship` skill).

## 2. What was borrowed

- **Reproduce first; a failing test is the proof.** Every practitioner write-up on agent bug fixing converges on the same order: reproduce, write the test that goes red, fix until it goes green, keep the test. Anthropic's own playbook adds: commit the failing test and forbid the agent from editing it while fixing. (Spotdev's summary of the Anthropic and OpenAI playbooks; builder.io's "a failing test, the patch, the same test passing" as what a reviewer needs; the obra/superpowers `systematic-debugging` and mattpocock `diagnosing-bugs` skills installed on this machine.)
- **Root cause before any fix; one hypothesis at a time; three failed fixes means the design is wrong.** From `systematic-debugging` ("no fixes without root cause investigation first").
- **A tight feedback loop is the skill.** From `diagnosing-bugs`: the reproduction must be red-capable (asserts the user's exact symptom), deterministic, fast and agent-runnable; "could not reproduce" is a valid, reportable outcome, not a reason to guess.
- **Blast radius and similar occurrences.** From the SpecOps bugfix template (regression risk analysis before the proposed fix) and the bluetape bugfix skill (record affected files and public contract; run broader tests in proportion). The diagnosis lists sibling call sites with the same mistake and says fix now or follow-up ticket.
- **Severity is not priority.** A hotfix changes scheduling and brief count, never testing, approval or production safety (the team's `bugfix-process.md`, and the Oniro bug policy's Fix / Defer / Mitigate / Hotfix split).
- **Keep scope narrow.** Agents spiral: many files touched, the bug still there. The fix is the diagnosis's Fix section and nothing else; the review lens reports unrelated changes as findings.

Sources read on 2026-11-04: spotdev.co.uk "working method for AI coding agents"; builder.io "build an agentic software factory starting with one bug"; webreference.com agentic workflows; localskills.sh on debugging skills; ymchoi/qbpowers diagnose-bug; adaptationio bugfix subagent chain; undeadlist claude-code-agents bug-fix; the SpecOps PR #5 bugfix template; bluetape4k bugfix skill; GitScrum and Plane triage guides; the Oniro bug policy; `~/Projects/moxie-portal-git-workflow/docs/engineering/git-workflow/bugfix-process.md`.

## 3. The process

One conductor, `/bugfix`, in the shape of `/feature`: it dispatches workers, checks their files on disk, and briefs the human at each gate. Stages, by level:

| Level | Stages | Lenses | Models |
|---|---|---|---|
| **L0 Tweak** | one build (regression test first when there is a seam, then the fix) → `npm run check`, `npm run build` → the human looks at the diff. The request is the go-ahead. | none; the diff brief | Opus Foreman; Sonnet build |
| **L1 Small** | triage (usually no questions) → the Foreman's own **diagnosis card** (cause by reading, ≤ 3 files or a narrow investigator question) → *approve* → fix (test red → fix → green, logged) → checks → the human tries it → review | `bug-review-fix` | Opus |
| **L2 Standard** | triage → *go* → **reproduce** (worker: failing test committed on the fix branch; briefed but no stop when it succeeds, since the triage yes covers both) → **diagnose** (worker: hypotheses, cause, blast radius, similar occurrences, fix, regression seam, risks, acceptance) → *approve* → fix → **verify** (tester: red→green proof, related suites, check, build, evidence specs) → the human tries it → review | `bug-review-fix`, conventions, plus permissions / db / errors / ui / performance when the diff touches their area | Opus; Sonnet tester |
| **L3 Risky** | L2, plus a Fable second look at the diagnosis and at the review | every lens plus `feature-fable-check` | Opus; Fable at diagnose and review |

The level floor is the feature workflow's (migrations, auth, scoping → L3; new columns, office visibility, email, shared config → L2). A **hotfix** (S1 at triage) runs the job's level with the triage brief cut to what reproduction needs, and the ship stage follows `bugfix-process.md`'s exception: PR #2 to `main` only with the release owner's word, then a sync PR to staging.

**Gates.** Triage's yes covers creating the `fix/` branch, its worktree and the matching org branch, reproducing (a test file and one commit), and diagnosing (read-only). `npm ci` is asked in the same brief as a Decision. The diagnosis's approval by version plus "fix" covers the code and test changes its Fix section names, one commit, and the local checks. Everything on the feature workflow's "still asked separately" list stays asked (databases, migrations, servers, email, installs, pushes, PRs, reviewer requests). Never skippable: the diagnosis (or the L1 card) is approved before anyone fixes.

**Three exits before the fix.** Triage or reproduction can end the job honestly: *not a bug* (a change request; the brief proposes `/feature` with the same ticket), *already fixed* on main (say which commit and whether it is deployed), *cannot reproduce* (what was tried; the human adds information, accepts a fix by inspection at L1, or closes it).

**Why not just ask Claude Code to fix it.** That is L0, and it is right for a typo. For anything else the one-prompt fix skips the three things that make a bug fix safe: proof it was reproduced, a test that keeps it fixed, and a reviewer who checks the fix against the cause rather than the symptom. The L1 route adds those in two briefs.

## 4. Artifacts (private folder, as for features)

- `repro.md`: what was reported (quoted), environment, steps, expected vs actual, the failing check (path, command, red output), data needed, result REPRODUCED / NOT REPRODUCED / INTERMITTENT (rate).
- `diagnosis.md` (vN, the document the human approves): symptom, reproduction, hypotheses considered and how each was ruled out, root cause (file:line, why), blast radius and similar occurrences, fix (files and change), regression test (seam), risks (floor triggers), acceptance. `acceptance.md` and `dev-tests.md` are written with the same version.
- `implementation-log.md` (the red and green test output), `test-report.md`, `manual-test.md`, `review/`, `review.md`, `decisions.md`, `status.json`, `briefs/`.

`status.json` for a bug job: `kind: "bug"`, stages `triage`, `reproduce`, `diagnose`, `implement`, `test`, `review`, `pr1`, `pr2`, `staging-qa`, `pr3`. Starbase folds them into its stops: triage → Spec, reproduce → Investigate, diagnose → Plan.

## 5. Repository layout

The repository is split by who uses what, and the install script links each group into `~/.claude`:

```
common/      shared by both workflows
  skills/workflow-common/   worker-rules, git-workflow, status-json, brief, lock, review-lens-rules,
                            review-facts, evidence, checklists/   (→ ~/.claude/skills/workflow-common)
  agents/                   feature-implementer, feature-tester, feature-reviewer, feature-review-*,
                            feature-fable-check                    (→ ~/.claude/agents)
feature/     the feature workflow
  skills/                   feature, feature-spec, feature-refine, feature-investigate, feature-plan, feature-wireframe
  agents/                   feature-spec-writer, feature-wireframer, feature-investigator, feature-planner
bugfix/      the bug-fix workflow
  skills/bugfix/            SKILL.md, levels.md, triage.md, templates.md
  agents/                   bug-reproducer, bug-diagnoser, bug-review-fix
tools/       standalone skills either workflow or a person uses
  skills/                   wireframe, ship, review-walkthrough, uat-guide
```

Shared agents keep their `feature-` names: renaming them would break every dispatch in both skills and Starbase's crew mapping for no gain. Their descriptions say they serve both conductors. The files that moved out of `skills/feature/` leave a one-line stub behind for jobs already running (delete the stubs after 2026-12-01).

## 6. Starbase

- A new job of kind **Bug fix** starts `/bugfix <description>` when the installed skills include `bugfix`; otherwise `/feature … (This is a bug fix.)` as before. Resuming a bug job also uses `/bugfix`.
- Level defaults for a bug job: the skip list names bug stages and the reviewers default to `bug-review-fix` (L1) or the bug lens set (L2+), chosen by `kind` in `normalize`.
- `status.json` accepts the three bug stages; the stops map them (triage → Spec, reproduce → Investigate, diagnose → Plan). The crew shows `bug-reproducer` as the tester's member, `bug-diagnoser` as the investigator's and `bug-review-fix` as the reviewer's; the reviewer picker labels the bug lens **Examiner**.
- Messages and docs that named `~/.claude/skills/feature/status-json.md` (and the other shared files) now name `~/.claude/skills/workflow-common/…`.

## 7. Not doing

- No separate `urgency` option field: a hotfix is a triage decision recorded in `decisions.md` and the Foreman's notes.
- No bug-specific wireframes, spec or refine stages.
- No renaming of shared agents.
- No change to the three PR stages or to the `ship` skill beyond naming the hotfix route it already documents.
