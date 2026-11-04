# Bug-fix templates

Private engineering artifacts. Keep each proportional: a small bug fills most sections in a line. Write "None." rather than deleting a section. `acceptance.md` and `dev-tests.md` use the feature templates in `~/.claude/skills/feature-plan/plan-templates.md` (the same short observable lines; "ready for staging" and the hand tests), written with the same version as the diagnosis.

## repro.md (the reproducer writes it)

```markdown
# <Bug title>: reproduction

| | |
|---|---|
| **Repro version** | 1 |
| **Date** | YYYY-MM-DD |
| **Ticket** | ORBIT-<n> · <url> |
| **Repository** | <path> · branch <name> · worktree <path> · base <sha> |
| **Result** | REPRODUCED / NOT REPRODUCED / INTERMITTENT (<n> of <m> runs) |

## Reported
> <the ticket or request, quoted as given; the steps, user, record and environment the human added>

## Environment
<production / staging / local · role and office · data it needs · anything redacted>

## Steps
1. <what a person does>
2. <…>
**Expected:** <…>
**Actual:** <…>

## The failing check
- **File:** `app/src/…/<name>.test.tsx` (committed as `<sha>` on the branch, `test(<area>): reproduce ORBIT-<n> …`)
- **Command:** `cd app && npx vitest run src/…/<name>.test.tsx`
- **Asserts:** <the user's exact symptom, in one line>
- **Red output:**
  ```
  <the relevant lines, redacted>
  ```
- **Why this seam:** <unit / component / integration; why a tighter one wasn't possible, if so>
- **Minimised to:** <what had to stay for it to fail; what was cut>

## Not reproduced / intermittent
<what was tried, each with its command and outcome; what would help (a record id, a user, a screen recording, a log); for intermittent, the rate and what raised it>

## Checks
**Run:** <commands actually run>
**Proposed, not run:** <checks that need a yes: database, server, email>
```

## diagnosis.md (the diagnoser writes it; the human approves it by version)

```markdown
# <Bug title>: diagnosis

| | |
|---|---|
| **Diagnosis version** | 1 |
| **Date** | YYYY-MM-DD |
| **Basis** | repro.md v<n> (<result>) · commit <sha> · ticket ORBIT-<n> |
| **Level** | L<n> |
| **Approval** | Not approved |

## Symptom
<one or two lines, in the user's terms; the ticket quote when it is short>

## Reproduction
<the failing check from repro.md: file, command, what it asserts; or "by inspection: the regression test is written first at fix time" when reproduce was skipped or at L1>

## Hypotheses considered
| # | If the cause is … | then … (the prediction) | Outcome |
|---|---|---|---|
| 1 | | | ruled out: <evidence> / confirmed |
| 2 | | | |

## Root cause
<file:line, and why: what the code does, what it should do, and how the symptom follows. One cause. A symptom with two independent causes is two diagnoses.>

## Since when
<the commit or PR that introduced it, from `git log`/`git blame`, or "always"; whether it is on staging or deployed>

## Blast radius
- **Callers / users of the changed code:** <path:line each; what each will see change>
- **Public contract:** <a signature, a route, an export, stored data: does it change?>
- **Sibling occurrences** (the same mistake elsewhere): <path:line — fix now / follow-up ticket> or "none found (searched for: …)"
- **Behaviour inventory:** <what else changes for a person once this is fixed; "nothing beyond the symptom" when so>

## Fix
- **Files:** <paths>
- **Change:** <2–6 lines: what changes and why it fixes the cause rather than the symptom>
- **Alternatives:** <the symptom patch and why not; a bigger fix and when it would win>
- **Size:** about <n> files, <n> lines; layer tags <db / api / ui / email>

## Regression test
<the repro test as it is, or: a better seam (path, what it would assert, why); plus any sibling test when fixing a sibling now>

## Checks
<the regression test command; the related suite; `npm run check`; `npm run build`; anything beyond those, marked read-only or needs a yes>

## Risks
<each migration, permission/role/office-scope change, email, shared config or data change the fix touches; "none" when none. Any one of them names the level floor it sets (job-options.md).>

## Acceptance
<the same numbered lines as acceptance.md v<n>: "It works when" and "It must not", 2–6 lines, observable>

## Change log
| Version | Date | Change |
|---|---|---|
| 1 | YYYY-MM-DD | Initial diagnosis |
```

## The L1 diagnosis card (the conductor writes it as `diagnosis.md` v1)

About 20 lines, the same headings cut to what the human needs to approve:

```markdown
# <Bug title>: diagnosis (card)

Version 1 · <date> · ticket ORBIT-<n> · L1 · commit <sha> · Not approved

**Symptom:** <one line>
**Reproduced:** by inspection (<file:line>); the regression test is written first at fix time
**Cause:** <file:line — why, in two lines>
**Since:** <commit / always>
**Siblings:** <path:line — fix now / follow-up> or none found (searched for: …)
**Fix:** <files; the change in 2–4 lines; about n lines; layer tags>
**Regression test:** <path, what it asserts>
**Checks:** regression test · `npm run check` · `npm run build` · <by hand: …>
**Risks:** none / <…, and the floor it sets>

## Acceptance (v1, also in acceptance.md)
1. <…>
2. <…>
```

## implementation-log.md: the red and the green

The implementer's entry for a fix carries both runs, so the tester and the fix lens can see the test was a real reproduction:

```markdown
## Fix (diagnosis v1)
- Regression test: `app/src/…/x.test.tsx` (committed <sha> by the reproducer | written first, committed <sha>)
- Red, before the fix: `npx vitest run …` → `FAIL … expected "No observation this month" to be visible, got "No observation this mo…"`
- Fix commit: <sha> `fix(dashboard): show every warning reason in full`
- Green, after: `npx vitest run …` → `1 passed`
- Other checks: `npm run check` ✓ · `npm run build` ✓
- Deviations from the Fix section: none
```

## test-report.md: the bug lines

The tester's report as for a feature (each acceptance line with PASS / FAIL / NOT RUN and evidence), plus at the top:

```markdown
**Regression test:** `<path>` — red before (from implementation-log.md: "<first line>"), green now (`<n> passed`)
**Related suites:** `npx vitest run <folder>` — <n> passed
**Reproduction steps (repro.md):** covered by the regression test / need the human's hand test (dev-tests.md 1–3)
```

## PR #1 body: the bug lines

In the Changes list of the short PR #1 body (`~/.claude/skills/ship/pr-body.md`):

```markdown
- **Cause:** `team-summary-strip.tsx:155` joined every reason on one truncated line
- **Fix:** one reason per line, wrapping, with a scroll past 8 people
- **Regression test:** `src/components/dashboard/team-summary-strip.test.tsx`

**Tests:** regression test red before, green after; `npm run check` and build pass; manual test passed locally.
```
