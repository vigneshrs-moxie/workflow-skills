# PR body skeletons

The organisation's PR template (`.github/PULL_REQUEST_TEMPLATE.md` in the git workflow docs) is the source; these are its sections filled the way the team writes them: short, concrete, nothing claimed that didn't run. PR #1 is the short form below; PR #2 and #3 keep the section headings (drop the checkbox lines you don't need) and carry the full detail, and end every body with the attribution line your session carries for pull requests.

## PR #1 (fork → same-named org branch)

Short: nobody reads a long PR #1. About 10 lines, no template sections, no limitations list, no review log, no test cases (those go in PR #2).

```markdown
## <TICKET>: <title>

<One or two sentences: what it lets someone do.>

**PR stage:** #1 Fork intake (fork → org `<branch>`)

**Changes**
- <3–5 bullets, one line each. A migration gets one line, with "apply before the code deploys" if it must.>

**Tests:** <one line: what passed, e.g. `npm run check` and build pass; manual test passed locally. Say "not run" for anything that didn't.>

**Decisions:** docs/decisions/<TICKET>-<slug>.md
```

The Decisions line links the job's decisions file when it rides this PR (`docs/decisions/ORBIT-0479-feedback-api.md`, committed as `docs(decisions): ORBIT-479 decisions`); leave the line out when there is none, or when Orbit still ignores `docs/decisions/`.

## PR #2 (org branch → staging)

```markdown
## Purpose and ticket

<Same paragraph as PR #1, updated.>

## PR stage

- [x] **#2 Staging:** `<org>:<branch>` -> `<org>:staging` (Raj's review required)

**Head:** `<org>:<branch>` @ `<sha>`
**Base:** `<org>:staging` @ `<sha>`
**Earlier-stage PRs:** PR #1 = #<n> (fork -> org branch), merged <date>.

**Scope check:** `git log moxie/staging..moxie/<branch>` lists only this task's <n> commits, plus the PR #1 merge and <n> merges of main into the branch. Diff against staging: <n> files (+a / −b), the same set as against main. <Or: what else is in it and why.>

<If it conflicts with staging: the draft notice, the conflicting files and who changed them on staging, and that checks re-run after the sync.>

## Changes

<As PR #1, trimmed to what a reviewer needs.>

## Test evidence

<PR #1's evidence, plus: CI on this PR (link), and anything re-run against staging.>

## How to test

<From the job's `dev-tests.md` and `acceptance.md`, when there are any; otherwise from what the change does.>

**Setup:** <branch or staging, database changes to apply, test users and roles, data needed>

**Dev tests** (tried by <who> on <date>):
1. <do this: you see that>
2. <…> (not run: <why>)

**Ready for staging** (check each before approving):
- [ ] <short outcome>
- [ ] <…>

## Risk, rollout, rollback

<As PR #1; migration numbers re-checked against the current staging; what to apply to the staging database before or after merge, if anything.>

## Review and approval

Raj: please review and submit an approving review on the latest commit. <Domain reviewers if any.> A human merges after approval and green checks.
```

## PR #3 (staging → main, the release summary)

```markdown
<One paragraph: what goes to production, for whom, and what customers notice.>

## Included

- #<n> <title> (<branch>, <author>, merged <date>): <one line on the change>
- …every PR merged into staging since main, not only the one that prompted this release…

## Database and configuration

- Migrations in this release: <`NNNN_name` … | none>. Order: <apply before deploy: … | after deploy (the automatic job): …>.
- Config, secrets, flags, dependencies: <none | …>

## Evidence

- Staging deployment: <sha / link>, tested by <who> on <date>: <what passed>; known issues: <…>
- CI and security on staging head: <link, result>
- Migration numbers checked against main: <ok | …>

## Release

- Release owner: <name>. Production trigger: <as configured; the owner confirms before merging>.
- Rollback: revert the merge commit; <what migrations leave behind>.
- After deploy: <smoke tests to run, by whom>.

Approval from someone other than the author is required before a human merges.
```

## Follow-up PR #1 (fork → org branch, the fixes for a review round on PR #2)

Title: `Follow-up for <reviewer>’s review on PR #2`. The dashboard writes this body itself when it opens the PR on Send back; from the terminal, write the same.

```markdown
Follow-up for <reviewer>’s review on PR #2 (<PR #2 link>), round <n>.

## What changed
- <short sha> <commit subject>
- …one line per commit on the fork branch not yet on the org branch…

## Answers
- <file:line>: fixed in <short sha>
- …the Fixed items only; the replies themselves are on PR #2…

The replies to each comment are on PR #2. Merging this brings the fixes onto PR #2.
```

## Sync PR (fork → org branch, after resolving conflicts with staging)

```markdown
Merge-conflict fix for PR #2 #<n>; no new feature work.

The diff is large because it carries every staging change this branch had not seen (<n> files). All of it is already on staging and reviewed there; PR #2 goes back to only this task's files once this merges.

## Hand-written changes

- `<file>`: <what conflicted and how it was resolved>
- …

Review the merge commit `<sha>` rather than the whole diff.

## Checks

<focused tests, `npm run check`, and the scope check `git diff --stat moxie/staging HEAD` listing only this task's files>

Rollback: revert the merge commit on the org branch.
```
