# Findings template

Private engineering artifact. Keep it proportional: a small enhancement may fill each section in a line or two. Write "None." rather than deleting a section.

```markdown
# <Feature name>: investigation findings

| | |
|---|---|
| **Findings version** | 1 |
| **Date** | YYYY-MM-DD |
| **Spec** | <path> · version <x.y> · status <status> |
| **Repository** | <path> · branch <name> · commit <sha> · working tree <clean / dirty: summary> |
| **Authorized scope** | <as recorded in workflow-status.md> |

## Summary
<3–6 lines: what exists today, the biggest constraints, what blocks planning.>

## Evidence by requirement
| FR / AC | Current behavior or capability | Label | Source |
|---|---|---|---|
| FR-001 | | Verified / Unknown / Implication | path:line |

## Reusable pieces
- <component, helper, pattern> — <path> — <how it could serve which FR>

## Permissions and data relationships
- <finding> — <path:line>

## Delivery, scheduling and notification capabilities
- <finding, including how test email is kept from real recipients> — <path:line>

## Test patterns and commands
- <how tests are organized; commands discovered from package scripts or docs; whether they write data>

## Branch, PR and release constraints
- <base branch, PR target, migration order and release rules found> — <source>

## Discrepancies and conflicts
| Topic | Document says | Repository says | Needs decision by |
|---|---|---|---|

## Unknowns
- <fact not determinable read-only> — <how it could be found, as a proposed check>

## Product decisions raised by the evidence
| ID | Question | Affects | Proposed route |
|---|---|---|---|
| P-1 | | FR-00x | return to /feature-refine / /feature-spec |

## Spec impact
Requirements the code contradicts, sharpens or makes much larger. Empty means the spec fits the code as written.
| FR / AC | What the code shows | Proposed spec change or question |
|---|---|---|

## Scope assessment
<Unchanged from the spec's route, or: substantially larger because …; propose /feature-refine for P-x.>

## Checks
**Run:** <read-only commands actually run>
**Proposed, not run:** <checks that need approval or could write data>

## Change log
| Version | Date | Change |
|---|---|---|
| 1 | YYYY-MM-DD | Initial findings |
```
