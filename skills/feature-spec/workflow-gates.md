# Feature workflow: routes, gates and records

Shared reference for the feature workflow: the stage skills `/feature-spec`, `/feature-refine`, `/feature-investigate`, `/feature-plan`, the conductor `/feature`, and the `feature-*` worker agents. Each reads this file at the start of its run. Only the implementation stage, run by the conductor after approval, changes application code.

## Routes

- **Small enhancement:** clarify → *gate* → spec → *gate* → wireframe → *gate* → investigate → *gate* → spec update (when findings affect the spec) → *gate* → plan → *gate* → implement → *gate* → test → *gate* → independent review → *gate* → PR #1 → PR #2 → staging QA → PR #3 release. Clarify is the conductor's own questions before the spec is drafted (up to five, each with options and consequences; it may ask none and go straight to the spec). Wireframe draws the spec's screens for review when the spec names a screen, page, dialog, sheet or email, and is proposed for skipping when it names none; agreed screens go into the spec as a minor version before investigation.
- **Large feature:** the same, with refine → *gate* between spec and wireframe (the screens are drawn from the refined spec).
- **Quick change** (only when the human chooses it, in the job's options or in words): quick plan → *gate* → implement + local checks → the human's own manual test, when they asked for one (waits for their result) → review with the chosen reviewers (+ fix rounds within the quick plan) → *gate* → PR #1 → PR #2 → staging QA → PR #3. No spec, refine, investigation or plan documents; the quick plan (outcome, numbered acceptance criteria, files, checks, risks) is approved by version before coding. See `~/.claude/skills/feature/job-options.md`.
- **Levels** (the job's options): L1 runs the quick route, L2 the small, L3 the large. L0 (a tweak) is one build with no gate before it, the one exception to the approvals below; see job-options.md.

**The human's options.** The human can skip stages, hand over documents they already have (a spec, findings, a plan) to use instead of a stage's output, choose the review lenses, and ask for manual testing or Fable second looks, per job (`options.json` in the private folder; rules in `~/.claude/skills/feature/job-options.md`). Options choose process, never permission (except L0's one build, job-options.md): they are never a go-ahead or an approval. Skipping a stage removes that stage and its own gate, never the gate before the next stage that runs. Never skippable: the human's approval of every plan (quick, written or provided, and every new version) before anyone acts on it, approval of what will be built before coding (except L0, see job-options.md), and everything under "Still asked separately" below.

After review, the three PR stages follow the git workflow (`~/.claude/skills/feature/git-workflow.md`): **PR #1** fork → same-named org branch (you self-review and merge it yourself), **PR #2** org branch → `staging` (Raj's GitHub approval), **PR #3** `staging` → `main` (release owner). Pushing, opening each PR and requesting reviewers each need their own go-ahead; agents never approve, merge or deploy. No stage implies permission for a later one.

### Spec update after investigation

Investigation often shows the spec doesn't fit the code as it really is. Findings therefore end with a **Spec impact** list: requirements the code contradicts, sharpens or makes much larger, each with a proposed question or wording change. When the list is non-empty, the next proposed stage is a spec update (`/feature-refine <spec> <findings>` in post-investigation mode, on either route) before planning. The spec gets a new version; planning then uses that version. If the new version reaches code the findings did not cover, run a small follow-up investigation (findings v+1) first. When the list is empty, go straight to planning.

### Sizing

Judge **product scope and uncertainty**, not the length of the request or a guess at how many files change.

- **Small:** a narrow outcome on mostly established behavior (add Copy ID to an existing page, rename a field, add a filter using existing rules). One or a few consequential gaps are closed by focused questions inside `/feature-spec`, not a refinement interview.
- **Large:** several workflows, lifecycle states, new business rules or interconnected product decisions (Announcements: audience rules, channels, scheduling, dismissal, expiration and retraction must work together). These are indicators of overall scope; a single permission or notification change is not automatically large.
- The human can ask for `/feature-refine` on any feature.
- If investigation or planning shows a "small" change is substantially larger, explain the scope change, name the new decisions, and propose returning to `/feature-refine`. Wait for authorization.

Every route needs clear V1 requirements and observable acceptance criteria. Keep specs, findings and plans proportional to the change; size never waives approval before coding (L0 is the human's choice in options, never your sizing) or appropriate validation.

## The gate

A **gate** sits between every pair of stages that run (the quick route lists its own). A stage ends by presenting:

1. what it produced (artifact paths and exact versions),
2. the substantive changes or findings,
3. open questions and anything blocked,
4. the proposed next stage with its exact invocation,

and then **stops**. The next stage starts only on explicit human authorization.

What counts as authorization:

- The human, after the stage was presented, invokes the named next skill on the current artifact (for example `/feature-investigate <spec path>`), or says in words "go ahead with <stage>". That authorizes **that named stage only**, with any scope limits the human states.
- It does not approve the product spec, the findings, or any later stage.

What never counts:

- Finishing a stage, saving an artifact, or a readiness label such as COMPLETE.
- Silence, elapsed time, or an earlier broad request ("build Announcements end to end").
- Approval of an earlier stage, or approval of a different artifact version.

### Checking the gate at the start of a stage

Before doing the stage's work, read `workflow-status.md` and the input artifacts from disk; conversation memory is not the record. The record says whether these hold:

- The previous stage's entry shows it was **presented for review** at the artifact version now on disk.
- No later edit to an input artifact has made the reviewed version stale.

**The human's explicit go-ahead decides.** When the human explicitly tells you to run this stage (for example "I reviewed it, go ahead", or the invocation plus words saying so), proceed even if a check above fails: the human overrides the record. Mention the gap in one line (for example "spec stage was never formally presented; v0.3 not previously reviewed"), record their words and the gap in `workflow-status.md`, and continue with what they asked.

When there is no explicit go-ahead (a bare invocation) and a check fails, or the request is ambiguous: present the previous stage's handoff (paths, versions, open questions, proposed scope), say what is missing, and wait. Do not treat the wait as declined.

### Draft artifacts

- Investigation may run on a DRAFT or IN REVIEW spec when authorized; it discovers facts only. The spec keeps its true status.
- Planning on a spec that is not APPROVED, or with Open questions that block parts of V1, needs the human to say explicitly that **provisional planning** on that version is authorized and for what scope. Label conditional and blocked sections in the plan.
- Coding needs human approval of the current spec, the proposed solution, the test plan and the acceptance criteria (`acceptance.md`), by version. One explicit yes naming those versions is enough. On the quick route, or when the human skipped the spec or plan, the approved quick plan (or `requirements.md` plus the plan) by version stands in; it must state numbered acceptance criteria. Except L0, see job-options.md.

### What the implementation go-ahead covers

Once the human approves spec, implementation plan and test plan by version (or the quick plan, on the quick route) and says to implement:

- creating the feature branch and its dedicated worktree from the latest `moxie/main`, per the git workflow file (`~/.claude/skills/feature/git-workflow.md`); and the matching org branch, created once with the create-only `gh api` call in that file (never a push to the org);
- code and test changes the approved plan describes;
- one local commit per plan step (never pushed);
- **local checks** the approved test plan (or the quick plan's "How it's checked") lists that touch no shared data: lint, typecheck, in-memory unit tests (`npm run check`) and `npm run build`;
- on the quick route, the review with the chosen lenses and fix rounds that stay inside the quick plan.

Still asked separately every time: anything that writes to a database (for example `npm run test:db`), migrations, starting servers, anything that could send email, installing dependencies, pushing, opening PRs, requesting reviewers. Agents never approve, merge or deploy.

A product question, or a discovery that would change the approved plan, stops implementation and comes back to the human.

### Changes after review

- A request for changes keeps work in the current stage.
- A finding that needs a new product decision becomes a **proposed return** to `/feature-spec` or `/feature-refine`, then a gate. It is never an automatic stage switch.
- When requirements, findings or plans change materially, list which recorded approvals and authorizations they invalidate, mark them **superseded** in `workflow-status.md`, and return those artifacts for renewed review before dependent stages continue. A changed approved spec returns to DRAFT (see the spec skill's versioning rules).

### Stopping and blocked stages

- When the human says stop, stop at the end of the current message and record where things stand.
- When the next skill is missing, unavailable or blocked by permissions, give the exact invocation and the saved input paths. Do not claim the stage ran or work around the block.

## Readiness labels

Readiness is separate from approval status and from authorization.

- **Spec status:** DRAFT / IN REVIEW / APPROVED (by whom, date, version).
- **Refinement:** one of
  - **NOT REQUIRED**: small route; one-line reason.
  - **PROPOSED**: large route; `/feature-refine` recommended and waiting at a gate.
  - **COMPLETE**: every confirmed V1 requirement has observable acceptance criteria, and no unanswered product decision blocks the proposed V1 behavior.
  - **BLOCKED**: list the question IDs and the FRs each one blocks.
- **Spec readiness for investigation** uses the same rule as COMPLETE, applied to the small route's spec too.

## Private engineering folder

Engineering artifacts live outside the application repository and outside anything a reporter or recipient can reach (tickets, attachments, search, emails):

- the private destination the human supplies, or
- `~/.claude/feature-work/<feature-slug>/`

Contents: `workflow-status.md`, `options.json` (the human's job options, written by Starbase; workers only read it), `findings.md`, `implementation-plan.md`, `test-plan.md`, `acceptance.md`, `dev-tests.md` (or `quick-plan.md` / `requirements.md` stand-ins), and later `implementation-log.md`, `test-report.md`, `manual-test.md`, `review/`, `review.md`, `fable/`. The conductor also keeps `status.json` and `briefs/` for Starbase (format: `~/.claude/skills/feature/status-json.md`). The product spec stays wherever `/feature-spec` saved it and stays product-level.

## `workflow-status.md`

Every stage creates or updates it. Record only what actually happened; write "not recorded" rather than inferring.

```markdown
# <Feature name>: workflow status

**Feature slug:** <slug>
**Route:** QUICK (L0, L1) / SMALL (L2) / LARGE (L3) — <one-line reason>
**Options:** <level; skipped stages; provided documents; reviewers; manual test; Fable checks — or "defaults">
**Spec:** <path> · current version <x.y> · status <DRAFT / IN REVIEW / APPROVED>
**Refinement:** NOT REQUIRED / PROPOSED / COMPLETE / BLOCKED — <reason or question IDs>
**Repository:** <path> · branch <name> · commit <sha> · working tree <clean / dirty> (from investigation)
**Current stage:** <stage> · <in progress / presented for review / stopped by request>
**Next proposed:** `<exact invocation>`

## Artifacts
| Artifact | Path | Version | Based on |
|---|---|---|---|
| Spec | | | |
| Findings | | | spec vX, commit <sha> |
| Implementation plan | | | spec vX, findings vY, commit <sha> |
| Quick plan / requirements | | | request, commit <sha> |
| Test plan | | | spec vX, findings vY, commit <sha> |
| Implementation log | | | plan vN · branch <name> · commits |
| Test report | | | commit <sha> |
| Review | | | commit <sha> |

## Review and authorization log
| Date | Who | What they said or did (quote or invocation) | Artifact + version | Authorizes | Scope / limits | State |
|---|---|---|---|---|---|---|
| | | | | | | current / superseded (reason) |

## Option changes
| Date | Change | Noted in brief |
|---|---|---|

## Stage history
| Date | Stage | Outcome | Artifacts produced |
|---|---|---|---|
```

"Who" is the person named in the conversation, or "the user in this session" when no name is given. Never record a stakeholder's approval (for example Raj's) unless the human states that it happened.

## Moxie Orbit

Apply only when the repository, its instructions or the human identify the project as Moxie Orbit. Read the latest Orbit brief the human supplies (a file path or pasted text); when none is supplied, ask for it rather than relying on another chat.

- Claude Code does the repository investigation, implementation and review. Planning stays separate from coding.
- Git, branches and PRs follow the workflow in `~/Projects/moxie-portal-git-workflow/`, summarized in `~/.claude/skills/feature/git-workflow.md`: every branch starts from the latest `moxie/main` (never staging), same branch name in fork and org, a dedicated worktree per task, and the three PR stages. Report any conflict with a spec, brief or repo doc for a human decision.
- Plan a safe test environment with the correct schema and representative data, and make sure test email cannot reach real recipients.
- Detailed engineering plans and review records stay private to the tech team, never in reporter-accessible tickets, attachments, search or emails. Reporters keep access to their own submissions.
- Human approval of the spec, proposed solution and test plan comes before coding. On the quick route (the human's choice), the approved quick plan stands in for all three. Each PR stage needs its own go-ahead: PR #1 you self-review and merge yourself; PR #2 needs Raj's submitted GitHub approval; PR #3 is the release owner's. Agents never approve, merge or deploy.
- Gates apply between spec, refinement, investigation and planning (Orbit workflow decisions, 2026-10-12), for the stages that run; stages the human skips have none.
- Keep process overhead from blocking product or tracker improvements: stay proportional.
