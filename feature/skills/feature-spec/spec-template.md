# Product spec template

Copy this structure for new specs. Keep every heading, even when a section is short; write "None yet." rather than deleting a section. For a small enhancement keep each section to a line or two. When resuming or importing a spec with its own layout, keep that layout.

```markdown
# <Feature name>: Product Specification

| | |
|---|---|
| **Version** | 0.1 |
| **Status** | DRAFT |
| **Route** | SMALL / LARGE — <one-line reason> |
| **Refinement** | NOT REQUIRED (<why>) / PROPOSED / COMPLETE / BLOCKED (<question IDs>) |
| **Last updated** | YYYY-MM-DD |
| **Requested by** | <name or role, if known> |
| **Spec author** | <user> (drafted with Claude) |

## 1. Summary
<2–4 sentences: what it is, who it is for, why it matters.>

## 2. Problem statement
<What is hard, slow, risky or impossible today, and for whom.>

## 3. Goals
- <outcome the user or business gets>

**Non-goals:** <what this feature deliberately does not try to achieve>

## 4. Users and permissions
| Role | What they can do | What they cannot do |
|---|---|---|

## 5. V1 scope
<Short paragraph and bullet list of what V1 includes.>

## 6. Functional requirements
| ID | Requirement | Source |
|---|---|---|
| FR-001 | The system shall … | Confirmed (request) / Confirmed (decision D-002) |

## 7. Acceptance criteria
| ID | Covers | Criterion |
|---|---|---|
| AC-001 | FR-001 | Given …, when …, then … |

## 8. Main user workflows
### Workflow 1: <name>
1. <step from the user's point of view>

## 9. Error states and edge cases
| Situation | What the user sees / what happens |
|---|---|

## 10. Out of scope
- <item> — <why, or "deferred to Future enhancements">

## 11. Future enhancements
- <idea> — <value it would add>

## 12. Open questions
| # | Question | Recommendation | Owner | Status |
|---|---|---|---|---|
| Q1 | | | User / Stakeholder | Open / Needs stakeholder review |

## 13. Decisions and assumptions
**Decisions**
| ID | Date | Decision | Decided by |
|---|---|---|---|
| D-001 | YYYY-MM-DD | | |

**Assumptions** (believed true, not yet confirmed)
- A-001: <assumption>

**Context** (current behavior or constraints observed, not requirements)
- <fact and where it came from>

## 14. Approval status
- **Status:** DRAFT
- **Approved by:** —
- **Approved on:** —
- **Approved version:** —

Approval needs an explicit human statement naming the version. Stage authorizations (investigate, plan) are recorded privately in `workflow-status.md`, not here.

### Change log
| Version | Date | Change |
|---|---|---|
| 0.1 | YYYY-MM-DD | Initial draft |

## Stage handoff
<see handoff-template.md; always the last section>
```
