---
name: ship
description: Move a finished branch through the team's three pull-request stages from the terminal, outside a /feature job or after one hands off. Fork branch to the same-named org branch (PR #1, you self-review and merge), org branch to staging (PR #2, Raj reviews), staging to main (PR #3, the release summary), plus the sync route when PR #2 conflicts with staging, and review rounds (changes asked for, fixed one commit per item, replies drafted, sent back through a follow-up PR #1 on the human's yes). It reads the git workflow docs, runs a read-only preflight (remotes, PR state on GitHub, only-my-commits check, merge simulation, migration numbers against main and staging, risk flags, CI), writes the PR body in the team's style, and opens the PR only when you say so. Never merges, approves, pushes to staging or main, or deploys. Use when the user says ship, open the PR, PR #1/#2/#3, release, staging PR, sync with staging, Raj asked for changes, review round, or asks what would go to main.
argument-hint: "[1 | 2 | 3 | release | sync | hotfix] [branch] [--dry]"
---

# Ship: the three PR stages

Input: $ARGUMENTS. The stage, branch and `--dry` (preflight and body only, open nothing) are optional; the preflight works the rest out.

## Rules that hold throughout

- **Source of truth:** `~/.claude/skills/feature/git-workflow.md` (the short version) and the docs it points to in `~/Projects/moxie-portal-git-workflow/docs/engineering/git-workflow/`. Read the short version first, then for the stage you are on: `fork-to-release.md` and `pull-requests.md` (all stages), `branch-sync.md` (PR #2), `staging-conflicts.md` (sync), `release-and-migrations.md` (PR #3), `bugfix-process.md` (hotfix). When this skill and the docs disagree, the docs win; say so.
- **You open PRs and push only with the human's explicit yes, one yes per action**, after showing exactly what will happen: remote, head repo + ref, base repo + ref, title. Push only to the fork. Creating the matching org branch is the exception: a standing yes, create-only, through `gh api` (step 1 of PR #1).
- **Never:** push to or merge into `staging` or `main`; merge or approve any PR; force-push; rebase a shared branch; apply migrations to a shared database; deploy; call anything deployed or approved that GitHub doesn't show.
- **Report what ran.** A check you did not run is "not run", in the PR body and in the reply.
- `<skill>` below is this skill's folder (`~/.claude/skills/ship` when installed).

## 1. Preflight (read-only)

From the repository checkout, on the task branch (or pass `--branch`):

```bash
# Python 3 (python3, or py -3 on Windows)
python3 <skill>/preflight.py [--stage 1|2|3|sync] [--branch <name>] [--org <owner/repo>] [--no-fetch] [--json]
```

It fetches both remotes (the one thing it writes: remote-tracking refs; `--no-fetch` skips it) and prints: remotes and which is the fork (the docs say `upstream`; this team's clones call the org remote `moxie`, and the preflight names it); the branch on local, fork and org, and the **worktree that holds it** (work there, never by checking the branch out in a checkout that holds other work); main and staging heads and how far apart they are; the PRs GitHub already has for the branch, the stage that follows, and for an open PR #2 its reviewers and reviews; the commits and files the stage would carry; a merge simulation against the stage's base, with who changed each conflicting file; migration numbers checked against main **and** staging (the CI script's rules) with the **target number** when they collide; risk flags from the paths; CI runs on the org head with their dates against the base's last move; and the `/feature` job folder that owns the branch, with its files and whether its `status.json` disagrees with GitHub.

Read it all. **BLOCKERS stop the stage** until fixed; each warning is either fixed or named in the PR body. Then give the human the starting state in one block, the `agent-rules.md` format trimmed to what is known:

```text
Task: …  Kind: feature | bug | maintenance
Fork: <remote> = <owner/repo>  Org: <remote> = <owner/repo>
Branch: <name> @ <sha>; fork <sha>; org <sha or absent>; base moxie/main @ <sha>
Stage next: PR #<n> <head> -> <base>; earlier PRs: …
Blockers / warnings: …
```

With a job folder, read what it has (the preflight lists its files: `workflow-status.md`, `review.md` or `review/*.md`, `test-report.md` or `manual-test.md`, `pr1-body.md`): that is the evidence and wording to reuse. The folder can be stale (a `status.json` still at an earlier stage); GitHub is the truth. Without a folder, the commits, the diff and the human's answer to one question ("ticket or spec, and what to say it does?") are the material.

**The stage's PR already exists** (the preflight lists it as OPEN): don't open another. Re-run the stage's checks against the current base, report what blocks it now (a migration number taken since, a conflict, foreign commits, a missing review, a body that states something no longer true), and offer, with a yes, to update its body (`gh pr edit <n> --repo <org repo> --body-file …`), set or clear draft (`gh pr ready`), or add the reviewer. **A fix after PR #1 merged** (a renumbered migration, a review change) takes the same road as a sync: commit it on the fork branch in its worktree, push with a yes, a follow-up fork → org PR that the human self-merges, and PR #2 picks it up; commits after Raj's approval need his fresh review. `--dry` stops after the report and the drafted body.

**Migrations:** a number collision is fixed with `cd app && npx tsx scripts/renumber-migrations.ts --base <org>/staging` (preview; `--apply` renames the folders and fixes references; `--check` runs the CI script). Pass `--base` explicitly: the script's default is `upstream/main`, which this team's clones don't have. Renumbering is a migration edit: it needs the human's yes, and the number must clear **both** main and staging (the preflight prints the target).

**Drafting with blockers:** write the body anyway, with the blocker named at the top the way the team does ("Draft: migration number to fix before review"), bracketed placeholders for evidence not yet produced, and no box ticked for a check that didn't run.

## 2. The stage

### PR #1: fork branch → same-named org branch

1. The org branch must exist from `moxie/main` at the task's base. If the preflight says it's absent, create it: `gh api -X POST repos/<org>/<repo>/git/refs -f ref=refs/heads/<branch> -f sha=<moxie/main SHA>` (never `git push` to the org, never main, staging or a release branch). Never point PR #1 at staging or at another task's branch.
2. If the branch is behind `moxie/main`, bring it in before pushing: `git merge <org>/main` (a merge, never a rebase once the branch is on the fork). Re-run the preflight.
3. Checks: ask once, with the recommendation to run them, then run what the human allows from `app/`: `npm run check`, `npm run build`, and focused tests. Record exact results. (In a `/feature` job these usually ran already; reuse the report and say when.)
4. Full-diff self-review material: with a job, `review.md`; without, read the whole diff and list what you checked and anything you'd change. The human reviews their own PR #1 and merges it; you don't.
5. **The decisions file** (a `/feature` job for a ticket, whose folder has `decisions.md`; otherwise skip this step): run `ground-control decisions <job> --worktree <worktree>`. It copies the job's `decisions.md` to `docs/decisions/ORBIT-0479-<short-title>.md` without its notes for agents and rebuilds the folder's index, `docs/decisions/README.md`; it never stages or commits. When the dashboard isn't installed, do the same by hand as `~/.claude/skills/feature/SKILL.md` (Records, "decisions.md in the repository") describes. Then `git -C <worktree> status --short` must show only those two files (anything else: stop and say what), and commit just them on the feature branch: `git -C <worktree> commit -m "docs(decisions): ORBIT-479 decisions" -- <the two paths>` (after `git add` of the same two). When the command refuses because Orbit still ignores `docs/decisions/`, say so in the reply and ship without the file; never edit Orbit's `.gitignore`. A later change to the job's decisions goes in the same way, as part of the next fix commit.
6. Body from `<skill>/pr-body.md` (PR #1), plus, when step 5 committed the file, one line linking it: `Decisions: docs/decisions/ORBIT-0479-feedback-api.md`. Title in the repo's style: `feat(area): what changed`, `fix(area): …`, or the batch style the team uses (`Oct 19 batch: …`).
7. With a yes: `git fetch <org>`, `git push -u <fork> <branch>`, then
   `gh pr create --repo <org repo> --head <fork owner>:<branch> --base <branch> --title "…" --body-file <scratchpad>/pr1-body.md`.
   Show the URL and say: you self-review and merge this one; nothing else runs until it has merged.

### PR #2: org branch → staging

1. PR #1 must show **MERGED** on GitHub (the preflight checks); the org head must contain the fork head.
2. **Only this task's commits:** `git log --oneline <org>/staging..<org>/<branch>` must list the task's commits plus the PR #1 merge. If the preflight lists foreign commits, main is ahead of staging: the main → staging sync PR must merge first (or, with a yes, rebuild the branch on staging per `branch-sync.md`). Don't open PR #2 carrying other people's work.
3. Merge simulation conflicts → the **sync** route below, then come back here. Migration numbers must pass against the current staging (and main). Re-run the preflight after anything moves.
4. Body from `pr-body.md` (PR #2) with the scope-check paragraph and the files-changed count a reviewer can compare on GitHub. Title as PR #1, or `… into staging: …` the way the team writes it.
5. With a yes: `gh pr create --repo <org repo> --head <branch> --base staging --title "…" --body-file …` (head is the **org** branch; `gh` resolves a bare branch name to the org's own branch when `--repo` is the org). Add `--draft` when conflicts remain. Request Raj's review only when the human says to (`gh pr edit <n> --add-reviewer <handle>`); his submitted approval and green, fresh checks are required before a human merges. After opening PR #2, build a review walkthrough for it with the `review-walkthrough` skill and give the human the link to send or attach to the Orbit ticket.

### PR #3: staging → main (the release summary)

1. Preflight `--stage 3`: every commit and every PR merged into staging since main, the diff, migrations, risk flags, CI on staging, and whether a release PR is already open.
2. Staging QA signoff is a human fact: ask who tested the deployed staging and what passed; don't invent it. The deployment and migration jobs can't be inspected from here; say so.
3. Body from `pr-body.md` (PR #3): **all** included PRs, not only the one that prompted the release; migrations and their before/after-deploy order (a migration whose column live code already reads goes before the deploy, by hand); config; evidence; owner; rollback; smoke tests. Title in the team's style: what goes to prod, e.g. `Portal Feedback, Role Template Copy and Collection Rate to prod`.
4. With a yes: `gh pr create --repo <org repo> --head staging --base main --title "…" --body-file …`. A merge commit, not a squash. Approval must come from someone other than the author; the release owner merges and watches the deploy.

### Sync: PR #2 conflicts with staging

Follow `staging-conflicts.md` step by step; the preflight already lists the conflicting files and the staging commits that touched them. In the task's worktree, clean tree: `git merge --ff-only <org>/<branch>` (after PR #1 merged), `git merge --no-ff <org>/staging`, resolve each conflict (read "Resolving a conflict" and "Things that bite" first), `npx prisma generate` if `schema.prisma` came in, typecheck and focused tests, commit with each conflict named, `git diff --stat <org>/staging HEAD` must list only this task's files, `npm run check`, then with a yes push to the fork and open the sync PR (fork → org branch) with the body from `pr-body.md` (Sync). After it merges, PR #2 is mergeable again; remove the draft notice.

### Hotfix (only when the human says so)

PR #1 as usual from a `fix/*` branch cut from main; PR #2 targets **main** instead of staging, with the human's explicit release-owner authorization recorded in the body; then a reviewed `main → staging` sync. Never choose this route yourself.

## 3. Review rounds

Opening a PR is half of it. Very often the reviewer (Raj, on PR #2) asks for changes. **A review round** is everything one reviewer asked for in one go: their "Request changes" review and its comments (or two comments or more within ten minutes of each other), plus the checks that failed on the same commit. A comment that arrives before the round goes back joins it; one that arrives after opens the next round. Ground Control groups a round for you and keeps it in the job folder (`review/rounds/round-<n>.md`); from the terminal, read the PR's reviews and comments yourself (`gh pr view <n> --repo <org repo> --comments`, `gh api repos/<org repo>/pulls/<n>/comments`), read only.

`<skill>/review-rounds.md` has the steps, the reply style and examples. In short:

1. **A plan per item first**, before changing anything: for each comment, its kind (change, question, nit, or a failed check) and what you will do (fix it, answer it, or keep it as it is and why). With a job folder, write it to `status.json` `prs[<n>].rounds` (state `planning`); show it to the human. Items the human left out are not worked on.
2. **Fix on the fork branch, in the job's worktree**, one commit per item or per small group, each commit message naming the comment it answers (`fix(feedback): name the id feedbackId (Raj's review, comment on api.ts:40)`). Run the checks the profile names (Orbit: `npm run check`) and the tests the change touches; say what ran in the round's `checks` line.
3. **Draft a reply for every comment**: short, polite, specific ("Fixed in a1b2c3d: renamed to `feedbackId`." / "Kept as it is: … because …" / the answer). A failed check gets no reply: the push runs it again. Each item's `reply` in `status.json`; the round's state `ready` when every item is done.
4. **Never push, reply, resolve, re-request or merge without the human's yes.** With Ground Control, one go on "Send back" does them all, in order, each listed first and logged: push to the fork, the follow-up PR #1, a reply per comment, resolve only the Fixed ones, ask the reviewer again. From the terminal, ask for one yes per action as everywhere in this skill.
5. **A change asked for on PR #2 travels through the fork:** commit on the fork branch → push to the fork (never to the org, never forced) → a **follow-up PR #1** (fork → the same-named org branch, body from `pr-body.md` "Follow-up PR #1", titled "Follow-up for Raj's review on PR #2") → the human merges it (you review and merge PR #1, as always) → PR #2 shows the new commits → ask Raj to review again (`gh pr edit <n> --repo <org repo> --add-reviewer <handle>`). A change asked for on PR #1 needs no follow-up: push, and the PR has it.
6. **The base moved and PR #2 conflicts:** follow the Sync procedure above (merge `staging` in, never rebase, so nothing is force-pushed), then send it back the same way.
7. **Disagreeing is fine:** "Won't change" with the reason, still replied to. A question only: just the reply and the re-request; nothing is pushed.
8. **Approved:** who merges comes from the profile's `prRoute` (Orbit: PR #1 you, PR #2 Raj, PR #3 the release owner). You never merge PR #2 or #3 from this skill; Ground Control's Merge always asks and only when the route lets the human merge.

## 4. After opening

- Reply with the URL, the exact head → base, what the human does next (merge PR #1 themselves; ask Raj; release owner), and what you did not run.
- With a `/feature` job folder: update its `status.json` `prs[<n>]` (`url`, `state: "open"`) and `stage` (`pr1`, `pr2`, `pr3`), and add a line to `workflow-status.md`, so the Workshop shows it. Record only what GitHub shows.
- End with the `agent-rules.md` "Final agent handoff format", filled with what is actually known; unknowns stay "no" or "not run".
