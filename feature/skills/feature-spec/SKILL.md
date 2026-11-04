---
name: feature-spec
description: Draft a product spec from a feature request (or resume a saved one), recommend the small or large route, then stop for human review.
argument-hint: <feature description | path to existing spec> [private folder]
disable-model-invocation: true
---

# Feature spec

Turn the request below into a **product specification**: a document a product stakeholder can approve and an experienced engineer can plan from. This is the first stage of the feature workflow. It writes the spec, its handoff and the private workflow record, then stops at a **gate** for human review.

Request: $ARGUMENTS

If the request is empty, ask for a one- or two-sentence description and stop.

If the request names an existing spec file, **resume** it: re-read the file and its `workflow-status.md`, continue from its current version, and keep its layout. Never restart a saved spec.

Read [workflow-gates.md](workflow-gates.md) now: routes, sizing, the gate, readiness labels, the private folder and the `workflow-status.md` format all live there.

## Ground rules (every phase)

- **Three labels, always kept apart.** Every statement about the feature is one of:
  - **Confirmed**: the user said it, or it is in the request.
  - **Recommended**: your suggestion. Stays recommended until the user accepts it.
  - **Open**: unknown, waiting on the user or a stakeholder.
  A recommendation becomes a requirement only when the user says yes to it. Business rules (who may do what, limits, money, timing, notifications, data retention) come from the user; when you need one, propose it as Recommended or ask.
- **Facts are investigation's job; decisions are the user's.** Questions about current behavior, data or capability go in the handoff's "Facts to verify in investigation". Read docs the user supplies and the repo's `CLAUDE.md` / `AGENTS.md`; leave code exploration to `/feature-investigate`. Current behavior is a fact about today, not an approved requirement.
- **Plain language.** Write for a product stakeholder: short sentences, no AI or process jargon, no framework names, endpoints, tables or schemas. Technical constraints the user states go in "Decisions and assumptions" as constraints, in product terms.
- **Lean V1.** Favor the smallest version that solves the core problem well. Push anything that adds complexity without clear value into Future enhancements.
- **Proportional.** A small enhancement gets a concise spec; a large feature gets the full treatment.

## Phase 1: Understand

Read the request and any context the user gives. If you are in a repository, read its `CLAUDE.md` / `AGENTS.md` and any product docs it points to, for business rules and doc conventions.

Write a short **Understanding** in chat:

- The problem being solved
- Who uses it (roles)
- What a user can do or know afterwards that they cannot now
- Confirmed requirements
- Missing information that changes the product

Done when every item above is filled or explicitly marked Open.

## Phase 2: Propose and save the draft

Write an initial **proposal** in chat, sized to the feature. For a large feature be generous with ideas; for a small one, a few lines.

- Feature overview (2–4 sentences)
- User problems and goals
- Main workflows (numbered steps from the user's point of view)
- Recommended features, each tagged **V1** or **Later**, with one line on why
- Suggested V1 scope
- Future enhancements / nice-to-haves

Think through, and suggest where useful: user experience, permissions and roles, empty and error states, edge cases (duplicates, concurrent edits, missing data, very large volumes), reliability (what the user sees when something fails), auditability, and how it fits the workflows people already use. Every suggestion stays labeled Recommended.

Then create the spec file (see **Saving**) as version 0.1, status DRAFT, and tell the user its path.

## Phase 3: Scope and readiness

Assess the draft against the sizing rules in [workflow-gates.md](workflow-gates.md) and state the proposed route in **one sentence** with its reason.

**Small enhancement:**

- If one or a few consequential product answers are missing, ask **focused questions**, one per message, highest impact first, in this format:

  ```
  **Q<n>: <short title>**
  <the question, with options if there are a few clear ones>

  Recommended: <your default>. <one or two lines on the tradeoff>
  ```

  After each answer: update the spec (Confirmed / Recommended / Open, FRs, ACs, decision log with today's date), bump the minor version, say in one line what changed, then ask the next question or move on.
- Ask only what would change what gets built. "Not sure", "ask <someone>" or "skip" leaves the item **Open** with your recommendation attached and its disposition (blocks FR-x / deferred outside V1 / answerable by investigation); it never adopts your default.
- Set **Refinement: NOT REQUIRED** with the reason, in the spec header and handoff.

**Large feature:**

- Leave the detailed interview to `/feature-refine`. List the unresolved product decisions as Open questions with recommendations, ordered by impact.
- Set **Refinement: PROPOSED**.
- If the spec already records a completed interview, say so; `/feature-refine` will reuse it and run only its readiness check.

Done when the route is stated, the Refinement label is set, and (small route) every consequential gap is answered or recorded as Open with a disposition.

## Phase 4: The specification

New specs follow [spec-template.md](spec-template.md): header block, then the 14 numbered sections, then the handoff. A resumed or imported spec keeps its own layout. Content rules:

- **Functional requirements** are numbered `FR-001`, `FR-002`… and never renumbered once written; a dropped FR is struck through and marked "Removed (v0.x): reason" so references stay stable. Only Confirmed items become FRs. Recommendations not yet accepted live in Open questions.
- **Acceptance criteria** are numbered `AC-001`… and each cites one or more FR IDs. Write them as observable behavior: Given / When / Then, or "A <role> can…" / "The <screen> shows…". A tester must be able to check each one by using the product. Every FR has at least one AC.
- Error states and edge cases say what the user sees, not how the system handles it internally.

## Saving

One file per feature, updated in place across the whole conversation and later sessions.

- **In a repository:** look for an established spec location (e.g. `docs/plans/`, `docs/specs/`, `docs/product/`) and follow its naming pattern. If none exists, propose `docs/plans/YYYY-MM-DD-<feature-slug>-product-spec.md` and confirm with the user before writing.
- **Outside a repository:** ask where to save it before writing.
- **Workflow record:** create or update `workflow-status.md` in the private folder (the one the user supplied, else `~/.claude/feature-work/<feature-slug>/`), using the format in [workflow-gates.md](workflow-gates.md).

**Status and version**

- New file: version 0.1, status **DRAFT**.
- Each substantive change bumps the minor version and adds a change-log row.
- **IN REVIEW** when the user says it is ready for stakeholders.
- **APPROVED** only when a human explicitly says the spec is approved and names or clearly means this version; record who, the date and the version in Approval status, and set version 1.0. A request for a handoff or for the next stage is not approval.
- Any edit after approval returns the status to DRAFT, bumps to 1.1, says so, and marks the approval superseded in `workflow-status.md`.

## Phase 5: Handoff and stop

1. Re-read the spec file and fix gaps: every FR has an AC, every AC cites a real FR, no Recommended item sits in V1 scope.
2. Write the handoff in [handoff-template.md](handoff-template.md) format as the last section of the spec, and print it in chat. Next stage: `/feature-investigate <spec path>` on the small route, `/feature-refine <spec path>` on the large route.
3. Update `workflow-status.md`: current stage "feature-spec · presented for review", spec version, route, refinement label, next proposed invocation.
4. Present the gate: spec path and version, status, route and why, open questions, and the proposed next invocation. Ask the user to review the spec and the proposed route (including any refinement skip).
5. **Stop.** The next stage starts only when the human invokes it or explicitly authorizes it.

Done when the handoff is saved in the spec, `workflow-status.md` shows "presented for review" at the current version, and the gate is presented.

## Scope boundary

This skill writes the spec and `workflow-status.md`, nothing else. Code exploration, implementation, test plans, branches, commits, PRs, ticket updates, messages, emails and deployments belong to later, separately authorized stages; when the user asks for one mid-spec, say which stage owns it and offer to finish or pause the spec first.

Follow the current repository's instructions and business rules where they apply. For Moxie Orbit, also apply the Orbit section of [workflow-gates.md](workflow-gates.md) and state its approval rules in the spec's Decisions and handoff.
