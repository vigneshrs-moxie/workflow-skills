---
name: feature-refine
description: Run the detailed product interview on a saved large-feature spec, one question at a time, then stop for human review before investigation.
argument-hint: <path to spec> [private folder] [context file paths]
disable-model-invocation: true
---

# Feature refine

The product interview for a **large feature**: several workflows, lifecycle states or interconnected business rules. It updates the saved spec in place until V1 is ready, then stops at a **gate**. It runs in the main conversation because it talks with the user.

Input: $ARGUMENTS

Read `~/.claude/skills/feature-spec/workflow-gates.md` first: routes, the gate, readiness labels, the private folder and the `workflow-status.md` format live there. Spec content rules (labels, FR/AC numbering, versioning, approval) are the ones in `~/.claude/skills/feature-spec/SKILL.md` (Ground rules, Phase 4, Saving); follow them here.

If no spec path is given, ask for one and stop. A feature with no saved spec starts with `/feature-spec`.

**Post-investigation mode.** When the input includes a `findings.md` (on either route), this run is the spec update after investigation: the questions come from the findings' **Spec impact** list rather than a fresh interview. Ask only those, update the spec to a new version, note in the change log which findings version drove it, and in the handoff say whether the new version reaches code the findings did not cover (then propose a follow-up `/feature-investigate`), else propose `/feature-plan <spec path>`.

## Step 1: Check the gate and load the record

Read from disk: the spec, its `## Stage handoff`, its decision log and approval status, `workflow-status.md`, and every context file the user supplies (briefs, decision records). Conversation memory is not the record.

Check the gate as described in workflow-gates.md. This stage is authorized when the spec stage was presented for review at the version on disk and the user has now invoked `/feature-refine` or asked for refinement in words. A user may ask for refinement on any feature, including one routed small. If the evidence is missing, stale or ambiguous, present the spec's handoff and wait, unless the human explicitly told you to go ahead, which overrides the record (see the gate rules).

Record the authorization in `workflow-status.md` (date, who, the invocation or words, spec version, scope) and set the current stage to "feature-refine · in progress".

Done when the gate is confirmed and recorded, or the handoff is presented and you are waiting.

## Step 2: Find what is unresolved

When importing a spec with its own layout, keep that layout; add only what is missing (stable IDs, change log, handoff).

List, in chat:

- **Product decisions** still unanswered that affect V1 scope, permissions, audience or data access, user workflows, timing and lifecycle, notifications, failure behavior, or observable acceptance criteria.
- **Contradictions** between requirements, decisions or context files.
- **Facts** that only the repository can answer. These go to "Facts to verify in investigation", not to the user.

Skip anything already answered in the decision log or the recorded interview, and anything whose answer would not change V1. Solution design belongs to `/feature-plan`.

If nothing material is missing, say so, ask no questions, and go to Step 4. In post-investigation mode, Step 2 is the Spec impact list plus anything it contradicts.

## Step 3: Interview

Ask **one consequential question per message**, highest impact first:

```
**Q<n>: <short title>**
<the question, with a concrete example, and options if there are a few clear ones>

Recommended: <your default>. <one or two lines on the tradeoff>
```

Ask a follow-up when an answer is ambiguous. After each answer:

1. Update the **same spec file**: record the decision with today's date, revise affected FRs and ACs (IDs preserved), keep Confirmed / Recommended / Open separate, bump the minor version for substantive changes, add a change-log row.
2. Say briefly what changed, then ask the next question.

A recommendation becomes Confirmed only when the user accepts it. "Ask Raj", "not sure" or "skip" leaves the item **Open** with your recommendation attached and one disposition: **blocks** <FRs>, **deferred** outside V1, or **answerable by investigation**. Deferring never decides the behavior. Keep V1 lean; an exhaustive questionnaire is not the goal.

If the spec was APPROVED and a decision changes it, it returns to DRAFT per the versioning rules; mark the approval superseded in `workflow-status.md` and say so.

When the user says stop, stop after saving and record where the interview stands.

## Step 4: Readiness check

Apply the readiness rule from workflow-gates.md:

- **COMPLETE** when every confirmed V1 requirement has observable acceptance criteria and no unanswered product decision blocks the proposed V1 behavior.
- **BLOCKED** otherwise, listing each blocking question and the FRs it blocks.

Readiness is not approval. The spec stays DRAFT or IN REVIEW unless a human explicitly approves a named version.

Done when every FR has been checked against its ACs and every Open question has a disposition.

## Step 5: Handoff and stop

1. Write the handoff in `~/.claude/skills/feature-spec/handoff-template.md` format as the last section of the spec (replacing the previous handoff) and print it. Next stage: `/feature-investigate <spec path>`. On BLOCKED, say which parts investigation could still usefully cover and which must wait for answers.
2. Update `workflow-status.md`: refinement label, spec version, "feature-refine · presented for review", next proposed invocation.
3. Present the gate: spec path, version and status; decisions made this session; blocking and deferred questions; facts for investigation; the exact `/feature-investigate` invocation.
4. **Stop.** Investigation starts only when the human invokes it or explicitly authorizes it.

Done when the spec on disk holds the new handoff, `workflow-status.md` shows "presented for review" at that version, and the gate is presented.

## Scope boundary

This skill edits the spec and `workflow-status.md` only. Repository investigation, plans, code, branches, tickets, messages and deployments belong to later, separately authorized stages.
