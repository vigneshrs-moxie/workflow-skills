---
name: feature-investigate
description: Establish current repository behavior and constraints for a reviewed feature spec, read-only, write private findings, then stop for human review before planning.
argument-hint: <path to spec> [repository path] [private folder] [scope limits]
disable-model-invocation: true
---

# Feature investigate

Establish the **facts**: what the repository does today and what constrains the feature. Produce private `findings.md`, then stop at a **gate**. This stage does not design the solution, write plans, or change the spec.

Input: $ARGUMENTS

Read `~/.claude/skills/feature-spec/workflow-gates.md` first: routes, the gate, the private folder, the `workflow-status.md` format and the Orbit rules live there.

If no spec path is given, ask for one and stop, unless your prompt names a stand-in the human's job options chose (`quick-plan.md`, `requirements.md` or a provided document) or a narrow question; then use that (see `~/.claude/skills/workflow-common/worker-rules.md`).

## Step 1: Check the gate

Read from disk: the spec and its `## Stage handoff`, `workflow-status.md`, and the context files the handoff lists.

This stage is authorized when the previous product stage (`/feature-spec` on the small route, `/feature-refine` on the large route) was presented for review at the spec version on disk, and the user has now invoked `/feature-investigate` or asked for investigation in words. A DRAFT spec is fine: investigation discovers facts only, and the spec keeps its status. If the route is LARGE and refinement is PROPOSED (never run), the refinement stage has not happened; present that and ask whether the user wants to skip it, recording their answer. If evidence is missing, stale or ambiguous, present the handoff and wait, unless the human explicitly told you to go ahead, which overrides the record (see the gate rules).

Record the authorization (date, who, invocation or words, spec version, any scope limits the user stated) and set the stage to "feature-investigate · in progress".

Done when the gate is confirmed and recorded, or the handoff is presented and you are waiting.

## Step 2: Confirm the checkout

Confirm with the user which repository and checkout to investigate when it is not obvious. Record without changing anything: path, branch, `git status` summary (clean or dirty), and HEAD commit. Read the project's current instructions (`CLAUDE.md`, `AGENTS.md`, docs they point to) and the brief the handoff lists.

## Step 3: Investigate, read-only

Scope it to the spec. A small enhancement needs the relevant component, its permission checks and nearby tests; a large feature needs the workflows and dependencies its FRs touch. Map evidence to FR and AC IDs.

Cover what applies:

- current behavior on the affected screens and flows
- permissions and roles, including direct-request access
- user, data and organization relationships (entities, branches, roles, accounts)
- relevant schema and migrations, and how migrations are numbered and released
- reusable components and patterns
- email, notification and scheduling capabilities, including how test email is kept from real recipients
- existing test patterns and the commands that run them
- branch, PR and release rules

Each item cites files and lines, and is labeled **Verified** (seen in code or config), **Unknown** (not determinable read-only), or **Implication** (what it means for the feature). Existing behavior is evidence, not an approved requirement.

Read-only means: no edits to application files, Git state, environment or settings; no installs, migrations, servers, notifications, or tests that may write data. Reading files and read-only Git commands are fine. List any further check you would want as **proposed**, separately from what you ran.

Done when every FR in V1 has its relevant evidence or a recorded unknown, and every "Fact to verify" from the handoff is answered or marked Unknown.

## Step 4: Record findings

Write `findings.md` in the private folder using [findings-template.md](findings-template.md). It names the spec version and repository commit it is based on.

Raise, without resolving:

- **Conflicts** between the supplied documents and repository instructions (for example base branch, PR target, release order). The human decides.
- **Product decisions the evidence raises.** Record them as proposed clarifications; do not edit the spec.
- **Spec impact.** List every FR or AC the code contradicts, sharpens or makes much larger, with a proposed change or question (see the template). This drives the spec update before planning.
- **Scope change.** If the work is substantially larger than the spec assumed, explain it, name the new decisions, and propose `/feature-refine <spec path>` for them.

## Step 5: Present and stop

1. Update `workflow-status.md`: repository revision, findings path and version, "feature-investigate · presented for review", next proposed invocation.
2. Present the gate: the key findings, unknowns, conflicts, proposed product clarifications, checks run versus proposed, and artifact paths and versions. Propose the next step: when Spec impact is non-empty, a spec update with `/feature-refine <spec path> <private folder>/findings.md`; when it is empty, `/feature-plan <spec path>` (findings at `<private folder>/findings.md` v<n>).
3. **Stop.** Planning starts only when the human invokes it or explicitly authorizes it.

Done when `findings.md` is saved, `workflow-status.md` shows "presented for review" at that findings version, and the gate is presented.

## Scope boundary

Writes only `findings.md` and `workflow-status.md` in the private folder. Implementation and test plans belong to `/feature-plan`; product changes belong to the product stages.
