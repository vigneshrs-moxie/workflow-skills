# Plan templates

Private engineering artifacts. Size each section to the change; a small enhancement may need a line per section. Write "None." or "Not applicable" rather than deleting a section.

## implementation-plan.md

```markdown
# <Feature name>: implementation plan

| | |
|---|---|
| **Plan version** | 1 |
| **Date** | YYYY-MM-DD |
| **Basis** | spec <path> v<x.y> (<status>) · findings v<n> · commit <sha> |
| **Planning authorization** | <full / provisional: scope>, per workflow-status.md |
| **Approval** | Not approved |

## Proposed solution
<A short description of the approach.>

## Alternatives considered
| Option | Why not chosen / when it would win |
|---|---|

## Requirement traceability
| FR | Plan steps | Status |
|---|---|---|
| FR-001 | S1, S3 | Ready / Conditional on Q<n> / BLOCKED on Q<n> |

## Steps
### S1: <name>
- Layers: <db / api / ui / email>
- Files / areas: <paths from findings>
- Change: <what changes>
- Depends on: <step or decision>

## Data and migrations
<new or changed data, migration order and numbering per findings, backfill, rollback>

## Permissions
<who can do what, including direct-request checks>

## Notifications and email
<what is sent, when, to whom; how tests are kept from real recipients>

## Failure cases
| Situation | Handling | Covers |
|---|---|---|

## Branch, PR and release
<base branch and PR target per findings; conflicts awaiting decision; migration/deploy order>

## Risks and open questions
- <risk or Q-id> — <impact> — <who decides>
```

## test-plan.md

```markdown
# <Feature name>: test plan

| | |
|---|---|
| **Test plan version** | 1 |
| **Date** | YYYY-MM-DD |
| **Basis** | spec v<x.y> · findings v<n> · implementation plan v<n> · commit <sha> |
| **Approval** | Not approved |

## Acceptance traceability
| AC | Test(s) | Level (unit / integration / DB / manual) | Status |
|---|---|---|---|
| AC-001 | T1 | | Ready / Conditional / BLOCKED on Q<n> |

## Tests
### T1: <name>
- Covers: AC-00x
- Setup / data: <representative data>
- Steps and expected result:

## Permission and leakage tests
<non-authorized roles, direct requests, data that must not appear for other users>

## Test environment and data
<environment with the correct schema; representative records; how email is captured or redirected so no real recipient is reached>

## Validation commands (proposed, not run)
| Command | Source (script/doc) | Writes data? |
|---|---|---|

## Independent review
<who or what reviews the implementation separately, and against which artifact versions>

## Not covered
- <gap and why>
```

## acceptance.md

What we accept as OK to push to staging and show stakeholders. A fellow developer reads it in a minute and checks each line before approving the PR. Approved by version with the plan; it goes in the PR #2 body.

**Keep every line short:** one plain sentence, about 12 words at most, something you can see in the app. No IDs, no tables, no "the system shall". Numbers only.

```markdown
# <Feature name>: ready for staging

Version 1 · from spec v<x.y> and plan v<n> · Not approved

## It works when
1. A manager can add a note on any customer.
2. The newest note shows first, with name and date.
3. <…>  (3–7 lines)

## It must not
1. Show notes to techs.
2. Slow down the customer list.

## Before staging
- [ ] `npm run check` and `npm run build` pass
- [ ] Dev tests pass
- [ ] No console errors on the changed pages
- [ ] Database: <none | apply migration `NNNN_name` before merge>
```

Track which lines are met in the job's records (test report, review), not in this file; tick nothing here.

## dev-tests.md

Quick tests the developer runs by hand on the job's branch (Starbase's Try it tab or a local server) before PR #1; the same list goes to the reviewer in PR #2. **One simple sentence each**: what you do and what you should see. Name the role only when it matters. No IDs, no tables, no "Covers" column.

```markdown
# <Feature name>: dev tests

Setup: <branch, migration to apply, test user(s), data needed>

1. Add a note "hello" on a customer: it shows at the top with your name.
2. Open a customer with no notes: you see "No notes yet".
3. Log in as a tech: there's no Notes tab.
4. Paste a 2,000-character note: it saves and wraps.
```

5–10 lines: the main path, an empty state, a role case, one edge case, and each "It must not" line. Every "It works when" line has a test. Results go in the job's `manual-test.md` ("all pass", or "3 fails: …"), not in this file.
