# Bug-fix workflow: levels, stages, gates and exits

The gates file for a bug job. The `/bugfix` conductor and every worker it dispatches read it first (a feature job's equivalent is `~/.claude/skills/feature-spec/workflow-gates.md`; the rules under "The gate" there apply here unchanged, and this file says what differs).

## Levels

The same four levels as a feature job, the same `options.json` fields and the same level floor (`~/.claude/skills/feature/job-options.md`, "Levels" and "Level floor"; Starbase's `level-rules.js`). What differs is the stage list.

| Level | Stages | Review lenses | Models |
|---|---|---|---|
| L0 Tweak (hotfix) | one build: the implementer writes the regression test first when there is a seam, then the fix → `npm run check` and `npm run build` → the human looks at the diff. The request is the go-ahead. No card. | none; you brief the diff | Opus conductor; Sonnet build |
| L1 Small | triage (usually no questions) → the conductor's own diagnosis card (approve) → fix (test red → fix → green) → checks → the human tries it → review | `bug-review-fix` | Opus |
| L2 Standard | triage (approve) → reproduce (worker; no stop when reproduced) → diagnose (approve) → fix → verify (the tester, with evidence) → the human tries it → review | `bug-review-fix`, `feature-review-conventions`, plus the lenses the SKILL.md table adds for what the diff touches | Opus; Sonnet tester |
| L3 Risky | L2, plus a Fable second look at the diagnosis and at the review | every lens, plus `feature-fable-check` | Opus; Fable at diagnose and review |

**Which level.** "Hotfix" in L0's name means the quickest route (one build, no card); it is not the S1 direct-to-main shipping exception below, which any level can take on the release owner's word. L0 when the cause is visible from the report (a typo, a wrong label, a wrong constant) and the fix is about 3 files and 50 lines in existing files with no floor trigger. L1 when the cause can be found by reading a few files and there is one obvious fix. L2 when it has to be reproduced to be sure, when the cause may be in more than one place, or when the fix touches data access, a shared component or a server action. L3 at the level floor (migrations, auth, scoping) or when the bug is in money, payroll, scheduling or anything a wrong fix would make worse. Severity (triage.md) is not the level: an S1 hotfix for a typo is L0.

**L0: the request is the go-ahead** (job-options.md says how; the same here). The implementer's prompt quotes the request as its authorization and its agent file's bug paragraph applies: regression test first when the seam is obvious, otherwise say so in the log. Anything past that one build needs the human's yes. A risk trigger or a change bigger than a tweak: don't build; propose L1 and give the diagnosis card.

**After every build, check the real diff** against the level, as job-options.md says. A fix that grew past its Fix section is the signal to stop and brief, not to continue.

## How level and skip combine

- `skip` may name `triage`, `reproduce`, `diagnose`, `test`, `review`. Feature stage names are ignored.
- **`triage` skipped:** no questions; the level must be set (else propose it in the first brief); at L2 and L3 the first brief is the reproduce brief, and the request plus the skip is the go-ahead for the branch and the reproduction, logged as such. Still never a go-ahead for `npm ci`, servers or the database.
- **`reproduce` skipped** (L2, L3): the diagnoser works from reading, as at L1, and the implementer writes the regression test first at fix time. The diagnosis says "not reproduced before the fix" in its Reproduction section.
- **`diagnose` skipped:** not possible. The diagnosis is approved before anyone fixes, always. A document the human provides as the plan (`provided.plan`) stands in for it, identified by path plus the first 8 characters of its sha256, and is approved by that; it must name the cause and the fix, else ask.
- **`test` skipped:** no tester, but you still run the regression test, `npm run check` and `npm run build` yourself, and the PR body says so.
- **`review` skipped:** no lens, but the pre-PR diff check from job-options.md still runs and `review.md` records it.
- **Hotfix** (S1 at triage): the same stages at the job's level; the triage brief asks only what reproduction needs; the ship stage follows the git workflow's `bugfix-process.md` exception only on the human's word that the release owner approved it. Urgency removes waiting, never the regression test, the review or the approvals.

## The gates

A gate sits between every pair of stages that run, as workflow-gates.md describes: the stage presents what it produced (paths and versions), the substantive findings, open questions, the proposed next stage, and stops. The next stage starts only on the human's explicit go-ahead, which authorizes that stage only. Finishing a stage, silence, elapsed time and an earlier broad request never count. The human's explicit words override the record (mention the gap, log it, carry on).

Two stages run without a stop in between: **reproduce → diagnose** when the reproduction succeeded (the triage yes covers both; the reproduce brief is written but not waited on). Everything else stops.

### What each go-ahead covers

**The triage yes** (L2, L3; or at L1 when a triage brief was given):
- creating the `fix/orbit-<n>-<slug>` branch and its worktree from the latest `moxie/main`, and the matching org branch create-only, per `git-workflow.md`;
- the reproduce stage: reading, running focused tests in the worktree, writing one test file (and a fixture if it must) and committing it on the branch;
- the diagnose stage: read-only, plus a temporary tagged log or throwaway test the diagnoser removes before it finishes;
- `npm ci` in the worktree only when the triage brief asked and the human said yes to that line.

**The diagnosis approval** (by version, plus "go" or "fix"), and at L1 the card's approval:
- at L1 and L0, creating the branch, worktree and org branch as above;
- the code and test changes the diagnosis's Fix section names, the regression test, one commit for each;
- the local checks: the regression test, `npm run check`, `npm run build`;
- a sibling occurrence only when the diagnosis or the human's answer says fix it now.

**Still asked separately, every time:** anything that writes to a database (`npm run test:db`), migrations, starting servers, anything that could send email, installing dependencies, each push, each PR, each reviewer request. Agents never approve, merge or deploy.

**Never skippable:** the human's approval of the diagnosis (or the L1 card, or the provided document) by version before anyone fixes, except L0's one build; and every new diagnosis version after a failed fix, a review or a manual test.

## Exits before the fix

Each is a brief with Decision 1, and the job ends (`stage_state: "done"`, `next_proposed` saying what) or continues on the human's answer. Never guess past one.

- **Not a bug.** The behaviour is as designed, or the ticket asks for something new. Say what the code does today (file:line) and propose `/feature` with the same ticket. Recommended when nothing is broken.
- **Already fixed.** Name the commit on `moxie/main` and whether it is on staging or deployed (the ticket's references; `git log`); propose closing, or a verification on staging by the human.
- **Cannot reproduce.** List what the reproducer tried (commands, data, rates), and offer: a) the human gives the missing piece (a record id, a user, a screenshot, steps), then reproduce again; b) at L1, a fix by inspection, where the implementer still writes the regression test first; c) close as cannot reproduce. Recommended: a.
- **Intermittent.** Reproduced at a rate; say the rate and whether the diagnoser can work with it (usually 20% and up). Propose going on, or raising the rate first (the reproducer's prompt names how).
- **Three failed fixes.** When the regression test is still red after the implementer's two attempts and one fix round, stop: the diagnosis is wrong or the design around it is. Brief that, propose a new diagnosis (v+1) at a higher level, and never a fourth attempt on the same diagnosis.

## Private folder

`~/.claude/feature-work/<slug>/` (or the private destination the human supplies), as for a feature job: `workflow-status.md`, `options.json`, `repro.md`, `diagnosis.md` (vN), `acceptance.md`, `dev-tests.md`, `implementation-log.md`, `test-report.md`, `manual-test.md`, `review/`, `review.md`, `fable/`, `decisions.md`, plus `status.json`, `briefs/` and `summaries/` for Starbase. Nothing from it is committed to the repository except the decisions file at PR #1.

### `workflow-status.md` for a bug job

The same file as workflow-gates.md shows, with these header lines in place of the spec and refinement lines:

```markdown
# <Bug title>: workflow status

**Job slug:** <slug> · **Kind:** bug · **Ticket:** ORBIT-<n> <url>
**Level:** L<n> — <one-line reason>
**Options:** <skipped stages; reviewers; manual test; Fable checks — or "defaults">
**Severity:** S1 hotfix / S2 / S3 — <from triage>
**Reproduction:** REPRODUCED / NOT REPRODUCED / INTERMITTENT (<rate>) / by inspection — repro.md v<n>
**Diagnosis:** diagnosis.md · current version <n> · <DRAFT / APPROVED (by whom, date)>
**Repository:** <path> · branch <name> · worktree <path> · base <sha>
**Current stage:** <stage> · <in progress / presented for review / stopped by request>
**Next proposed:** <one line>
```

The Artifacts table lists Reproduction, Diagnosis, Acceptance criteria, Dev tests, Implementation log, Test report, Review. The review and authorization log, the option changes and the stage history are as for a feature.
