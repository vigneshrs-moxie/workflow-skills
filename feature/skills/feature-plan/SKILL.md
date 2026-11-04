---
name: feature-plan
description: Draft a private implementation plan and test plan from a spec and reviewed investigation findings, then stop for human review before any coding.
argument-hint: <path to spec> [path to findings.md] [private folder] [scope limits]
disable-model-invocation: true
---

# Feature plan

Turn the spec and the **reviewed** findings into the private plan artifacts, `implementation-plan.md` and `test-plan.md`, plus the two the human hands on to the reviewer, `acceptance.md` (what it needs to be ready for staging) and `dev-tests.md` (one-line tests the developer runs by hand), all in [plan-templates.md](plan-templates.md); then stop at a **gate**. This stage proposes; it does not code.

Input: $ARGUMENTS

Read `~/.claude/skills/feature-spec/workflow-gates.md` first: the gate, draft-artifact rules, the private folder, the `workflow-status.md` format and the Orbit rules live there.

If no spec path is given, ask for one and stop, unless your prompt names a stand-in the human's job options chose (`quick-plan.md`, `requirements.md` or a provided document) or a narrow question; then use that (see `~/.claude/skills/workflow-common/worker-rules.md`).

## Step 1: Check the gate

Read from disk: the spec and its handoff, `findings.md`, `workflow-status.md`, the current project instructions and the brief the handoff lists.

This stage is authorized when the investigation was presented for review at the findings version on disk, and the user has now invoked `/feature-plan` or asked for planning in words. Then check the spec:

- **APPROVED, no blocking Open questions:** proceed.
- **Not approved, or blocking Open questions:** proceed only if the user explicitly authorized **provisional planning** on this spec version and stated its scope. Otherwise present the situation and ask. A plain `/feature-plan` invocation is not that statement.
- A small enhancement needs clear V1 behavior and observable ACs, not a refinement stage.

If evidence is missing, stale (spec or findings changed since review) or ambiguous, present the investigation handoff and wait, unless the human explicitly told you to go ahead, which overrides the record (see the gate rules).

Record the authorization (date, who, words or invocation, spec and findings versions, provisional or not, scope) and set the stage to "feature-plan · in progress".

Done when the gate is confirmed and recorded, or the handoff is presented and you are waiting.

## Step 2: Fix the basis

Record the exact spec version, findings version and repository commit the plans depend on. Check whether HEAD has moved since the findings; note it if so.

Use the reviewed findings rather than repeating investigation. Small read-only fact checks within the planning scope are fine. A material discovery that changes the reviewed basis stops dependent design: describe it, propose updated findings for renewed review, and wait.

## Step 3: Draft the plans

Write both files in the private folder using [plan-templates.md](plan-templates.md). Leave `findings.md` untouched.

- **Traceability:** every V1 FR maps to plan steps and every AC to at least one test.
- **Blocked decisions:** an unanswered business rule (audience, permission, timing, notification) is never filled with your default. Mark the affected design and tests **BLOCKED on Q<n>**, plan around them where safe, and propose the product stage that answers it.
- **Discovered, not assumed:** commands, schema names, migration numbering and branch rules come from findings or files you read; cite them.
- **Proposed, not run:** every check is a proposal. Running tests, migrations or servers is out of scope here.

Done when every V1 FR and AC is traced or explicitly marked BLOCKED, and every section of both templates is filled or marked "None.".

## Step 4: Present and stop

1. Update `workflow-status.md`: plan and test-plan paths and versions, their basis, "feature-plan · presented for review".
2. Present the gate: the proposed solution in a few lines, alternatives that matter, stages, data changes, the test strategy, blocked and conditional parts, unresolved questions, artifact paths and versions, and the spec's approval status.
3. State what coding needs: human approval of the current spec, this implementation plan, this test plan and `acceptance.md`, each by version (`dev-tests.md` goes with them). PR creation, merge and deployment need their own authorization.
4. **Stop.** Implementation is a separate request after that approval.

Done when both plans are saved, `workflow-status.md` shows "presented for review" at their versions, and the gate is presented.

## Revisions

A requested change keeps work in this stage: update the plan, bump its version, and say which earlier plan approvals are superseded. When the spec or findings change, the plans' basis changes too: update the basis versions and return the plans for review.

## Scope boundary

The application checkout stays read-only. Writes only `implementation-plan.md`, `test-plan.md`, `acceptance.md`, `dev-tests.md` and `workflow-status.md` in the private folder.
