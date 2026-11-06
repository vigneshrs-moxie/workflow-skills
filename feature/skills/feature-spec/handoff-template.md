# Handoff template

Shared by `/feature-spec` and `/feature-refine`. Save it as the **last section of the spec file**, replacing any earlier `## Stage handoff` or `## Technical planning handoff` section, and print it in chat. Keep it under one screen: it points into the spec rather than repeating it. It is product-level; engineering detail belongs in the private folder (see [workflow-gates.md](workflow-gates.md)).

When importing a spec with its own layout, append this section without restructuring the rest of the document.

The next stage re-reads this section from the saved file. A new session with only the spec and `workflow-status.md` must be able to continue.

```markdown
## Stage handoff

**Spec:** <path> · version <x.y> · status <DRAFT / IN REVIEW / APPROVED (by, date, version)>
**Prepared:** YYYY-MM-DD by <stage skill>
**Route:** SMALL / LARGE — <one-sentence reason>
**Refinement:** NOT REQUIRED (<why>) / PROPOSED / COMPLETE / BLOCKED (<question IDs>)
**Workflow record:** <private folder>/workflow-status.md

### In one paragraph
<What is being built, for whom, and the single most important outcome.>

### Decisions this stage recorded
- D-0nn: <decision> (YYYY-MM-DD)  — or "None this stage."

### Requirements and acceptance criteria
FR-001 … FR-0nn, AC-001 … AC-0nn (see the requirements sections). Highest-risk:
- AC-00x: <criterion>

### Open questions
| ID | Question | Blocks | Disposition |
|---|---|---|---|
| Q<n> | | FR-00x / nothing in V1 | blocking / deferred outside V1 / answerable by investigation |

### Facts to verify in investigation
- <unverified belief about current behavior, data or capability>

### Context
- <brief, decision record and other context file paths>
- <business rules and team rules that apply>

### Do not assume
- Recommended, Assumptions and Open items are not requirements.
- Current code behavior is context, not an approved requirement.
- This handoff is not approval. Each next stage needs explicit human authorization; coding needs approval of the spec, proposed solution and test plan.

### Next stage (waiting for human review)
`<exact invocation, e.g. /feature-investigate docs/plans/2026-10-12-copy-id-product-spec.md>`
<one line on what that stage will and will not do>
```
