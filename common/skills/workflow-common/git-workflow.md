# Git workflow for feature implementation

**Source of truth:** `~/Projects/moxie-portal-git-workflow/`, a clone of `github.com/vigneshrs-moxie/moxie-portal-git-workflow` that `install.sh` keeps up to date. If it is missing, tell the human to run `install.sh` from the workflow repo, and work from this summary meanwhile. Read its `CLAUDE.md`, then `docs/engineering/git-workflow/` (`fork-to-release.md`, `branch-naming.md`, `feature-process.md`, `agent-rules.md`, `pull-requests.md`, `release-and-migrations.md`) and `.github/PULL_REQUEST_TEMPLATE.md`. Those documents are marked "proposed" for the team, but the human has chosen to follow them. When this file and those documents disagree, the documents win; report the drift.

This file is the short version the conductor and workers act on.

## Remotes (verify every time with `git remote -v`)

Expected: `origin` = the developer's own personal fork, `moxie` = org `Moxie-Pest-Control-Phoenix/moxie-portal`. Each developer's fork differs, so read it from `git remote -v`; if the remotes don't match this shape, stop and ask. Never assume; never treat `origin/main` or `origin/staging` as authoritative.

## Orbit ticket first

Every new internal task (feature, bug, urgent fix, code-producing investigation, CI, chore, refactor, docs) needs a **real Orbit ticket before its branch exists**. Record its ID (`ORBIT-123`), URL, owner and agreed scope in the starting-state report. Until the Portal Feedback API/MCP exists, the human creates or finds it in Portal Feedback; afterwards use only that authorized interface. Never invent an ID or use `ORBIT-TBD`; with no ticket, stay read-only and ask. A ticket does not approve scope, pushes, PRs, merges or release. Urgent incidents: short intake, ticket recorded before the fix branch; Raj's emergency release authority is unchanged.

## Baseline

**Every task branch starts from the latest `moxie/main`, never `staging`** (human decision 2026-10-12). `staging` is only the PR #2 target.

## Branch name: the same in the fork and in the org

- Feature: `feature/orbit-<number>-<slug>` (e.g. `feature/orbit-123-ticket-comments`). No `-vN` suffix; a later increment gets its own ticket and number.
- Bug/hotfix: `fix/orbit-<number>-<slug>` (e.g. `fix/orbit-124-comment-save`). Also `ci/`, `chore/`, `docs/`, `refactor/` + `orbit-<number>-<slug>`. No ticketless path.
- Example numbers are illustrative; use the real ticket. One primary ticket per branch; never chain several IDs into the name (list extra tickets in the PR).
- Existing branches are never renamed, rebased, force-pushed or recreated to comply; `main`, `staging`, `mirror/*`, `dependabot/*` and revert branches keep their names. No `release/*` scheme.
- Short lowercase kebab-case. Before using a name, check it is free on both remotes: `git ls-remote --heads origin <branch>` and `git ls-remote --heads moxie <branch>`. Never overwrite or reuse someone else's branch.

## Starting a task (implementation stage)

1. Report the starting state in the format of `agent-rules.md` ("Report the starting state before editing").
2. `git fetch moxie --prune`, then create a dedicated worktree next to the repository: `git worktree add -b <branch> ../orbit-<slug> moxie/main`. One task = one branch = one worktree = one writer. Never work on top of an existing task worktree.
3. Create the **matching org branch** (`moxie:<branch>`, from the same `moxie/main` SHA) yourself, right after the worktree: `gh api -X POST repos/<org>/<repo>/git/refs -f ref=refs/heads/<branch> -f sha=<moxie/main SHA>`, with both values written out. The human has given a standing yes for this one action (2026-10-22); it is create-only (GitHub refuses it when the branch exists) and never targets `main`, `staging` or a release branch. Never `git push` to `moxie`. If the call fails because the branch exists, check it points at the base SHA and brief any mismatch instead of changing it.
4. Record branch, worktree path and base SHA in `workflow-status.md`.

## Commits

Small, reviewable, one per plan step, approved scope only.

Messages follow the common conventional style: `<type>(<area>): <what changed>`.
- Types: `feat`, `fix`, `test`, `refactor`, `chore`, `docs`. Area is a short, familiar name (`tickets`, `auth`, `email`).
- Imperative, lowercase, no trailing period, about 50 characters, at most 72. Say what changed in plain words; skip internal jargon, plan IDs and file lists.
- Add a short body only when the reason isn't obvious (one or two lines on why).
- Good: `feat(tickets): add copy ID button`, `fix(email): skip resend on retry`, `test(tickets): cover copy failure state`.
- Which commit belongs to which plan step is recorded in `implementation-log.md`, not in the message.

## Before PR #1

- Checks from `app/`: focused tests, `npm run check` (typecheck, lint, Vitest), `npm run build`. Record exactly what ran and the results; name anything skipped. Full CI does not run on PR #1, and a green secret scan is not CI.
- Inspect `git status` and the full diff for secrets, generated files, unrelated changes, migrations, auth/role/office impact.
- The consolidated multi-lens review (`review.md`) is the **code-review report** handed to the developer for their own full-diff self-review. Greptile or another approved AI reviewer is optional.

## PRs (each needs the human's explicit yes; agents never approve or merge)

| PR | Head → base | Gate |
|---|---|---|
| #1 intake | `<your-fork>:<branch>` → `Moxie-Pest-Control-Phoenix/moxie-portal:<same branch>` | Developer self-reviews and manually merges. Raj not required. |
| #2 staging | `moxie:<branch>` → `moxie:staging` | Fresh CI + security; **Raj's submitted GitHub APPROVED review**; a human merges. |
| #3 release | `moxie:staging` → `moxie:main` | Release owner; approval from someone other than the author; a human merges. Agents may draft the summary only. |

- Push only to the fork (`origin`), only with a yes; `git fetch moxie` and bring in `moxie/main` before every push. Ask before any rebase that would need a force-push.
- Fill the body from `.github/PULL_REQUEST_TEMPLATE.md` (in the workflow folder), including **Primary Orbit ticket**, **Additional Orbit tickets**, **Related branches and PRs**, and spec/demo/knowledge-base/requirement-approval links where they apply. Task PR titles carry the primary ID: `feat(feedback): ORBIT-123 add ticket comments`. A release PR lists every included ticket and PR from the actual diff. Never write `Closes #123` for ORBIT-123. Commit messages don't need the ticket ID.
- After each push or PR, register its URL on the ticket (authorized API/MCP when available; otherwise give the human the URL to paste into the ticket's **Branches** or **Pull requests** field). Never change ticket status or post a ticket comment as part of that. Check head repo+ref and base repo+ref at every stage.
- Open PR #2 only after PR #1 has actually merged, and never with the fork as head.

## Stop for the human before

DB migrations, roles/auth/office visibility, shared-environment data, secrets, external integrations, production infrastructure, or anything outside approved scope, unless the approved plan names that exact change. Never push to or merge into `staging`/`main`, apply migrations to shared databases, approve PRs, deploy, or mark anything deployed.

## Finishing

End with the "Final agent handoff format" from `agent-rules.md`, including the ticket ID/URL and exact branch and PR URLs.
