# Stacks: the coordinator stage

A **stack** is one big job split into **sections** that are built side by side. You, the parent job's Foreman, are its **coordinator**: you write the plan, and Starbase does the rest in code. Each section is a child job with its own worktree, branch, port and Foreman; Starbase starts them, merges each finished one into your branch in the plan's order, runs the checks after each merge, and waits for the human's go before anything is pushed. Stacks run only in Starbase on the human's own computer; in a terminal session, don't start one.

## When to propose one

Propose a stack only when the work splits into parts that each own their own files: two to six sections, each buildable and testable on its own, with few dependencies between them (an L3 change across several subsystems, a ticket too big for one review).

- **In your first brief**, when the ticket already looks that big, say so in one line ("This ticket looks big enough for a stack: …, about N parts") and write the same reason, one plain sentence, as `stack_suggested` in `status.json` (status-json.md). The Job page shows it with a "Run as a stack instead" button; the human's yes comes back as a message asking you to run it as a stack. Without that yes, carry on as a single job: the suggestion changes nothing by itself. Keep `stack_suggested` in later writes until the human answers, then set it to `null`.
- **In the plan brief**, propose one when the plan shows the split: say in one line why, and how many sections.

Their yes (the button, a message, or the plan brief's go-ahead) is the go-ahead to write `stack.md`; it does not start anything. A job started with "Run as a stack" (from the Inbox's Start as stack, or New job) is the same yes: write `stack.md` at plan.

## Writing `stack.md`

`stack.md` goes in your private folder. Write it with the Write tool, in exactly this shape; Starbase reads it and shows every problem in plain words on the Stack page.

```markdown
# ORBIT-512 · Work orders v2

The API and the screens touch different folders, so they build side by side; the screens need the API's shapes, so they wait for it. The help page stands alone.

## Section: api
The work order API: list, create and close, with its tests. One paragraph: what this section builds and how it is checked.
Owns: app/api/work-orders/**, app/lib/work-orders.ts
Depends on: none

## Section: ui
The work order screens, on the new API.
Owns:
- app/ui/work-orders/**
Depends on: api
Model: claude-sonnet-5-5
Effort: medium

## Section: docs
The help page.
Owns: docs/work-orders.md
Depends on: none

Order: api, ui, docs
```

- **Why it splits this way:** one short paragraph under the title, before the first section, in plain words a newcomer follows: which parts are independent (different files) and so build side by side, and why any part waits for another. The Stack page shows it at the plan check under "Why these parts", with what each dependency means.
- **One `## Section: <name>` per section.** The name goes into folder and branch names: lower-case letters, numbers and dashes, up to 40 (`api`, `work-order`). Each name once.
- **The brief** is the paragraph under the heading. It is the section's whole spec: the section skips clarify and spec and starts at plan from it, so say what it builds, what it must not change, and how it is checked.
- **`Owns:`** the files and folders the section may change, repository-relative, comma-separated or one `- ` line each; `*` matches within a folder, `**` across folders. Every section owns at least one path. **Owned paths don't overlap**: one file, one owner. A file two sections need goes to the one that changes it first; the other depends on it.
- **`Depends on:`** the sections that must have **merged** before this one starts, or `none`. No loops.
- **`Model:`** and **`Effort:`** (optional): override the stack's model and effort (Opus, high by default) for one section. Effort is `low`, `medium`, `high`, `xhigh` or `max`.
- **`Order:`** last: every section once, in the order they merge. A section comes after everything it depends on.

Then brief the human in one line: the plan is on the Stack page for approval, with how many sections and their order. Stop. (The Stack page calls sections "parts"; the files and Starbase's messages to you say "section". They are the same thing.) If they ask for a change (a note from the Stack page: "The person asks for a change to the stack plan…"), write `stack.md` again and stop again.

## What you never do

- **Never start a section yourself**, make its worktree or branch, or dispatch an implementer for it. Once the human approves the plan on the Stack page, Starbase starts the sections, at most the stack's number at once and within the global number in Settings → Workflow, in the plan's order as their dependencies merge. You don't decide who runs next.
- **Never merge a section by hand** and never write `stack.json`: Starbase writes it, and it is the stack's task list (read it to see where each section is).
- **Never push before you are told to.** "Merge on its own" on the Stack page lets merges happen without a yes; it never skips the push.

## Merges, and what you are told

Starbase sends you a message at each step; each is one line in `stack.json`'s log as well. Read it, act only as it says, and reply in a line or two.

- **"Section <name> is ready to merge."** Its own gates passed (its review is done). The human says yes to the merge on the Stack page (or, with "Merge on its own", it merges by itself when it is next in order). Sections merge only in the plan's order, never out of it.
- **"Section <name> is merged into <your branch>, and the checks passed (…)"** Starbase merged it into your branch with `git merge --no-ff` in your worktree and ran the repository's checks (its profile's `checks:` list) on the merged branch. Nothing for you to do but keep your records.
- **"The checks failed after merging section <name> … the merge was undone"** Your branch is back where it was, so it always passes. The failure went to that section's Foreman; at its third failure the section stops and the human decides.
- **A clash or files outside its owned paths:** nothing was merged and the files are named. The human hands the section back to its Foreman from the Stack page. If the plan itself is wrong (a file belongs to two sections), say so and propose a change to `stack.md`.
- **"Every section is merged."** The Stack page now asks the human go or no go for the push. Wait.

## The push

Only on **"The person said go on the Stack page: push <branch> to your fork now …"**: run exactly the `git push -u <fork remote> <branch>` it names, from your worktree. It asks for its own permission as usual, and the hard lines still apply: your fork only, never the organisation's repository. A no go means don't push. After the push, the job goes on as any other: PR #1 and the stages after it, each with its own go-ahead (SKILL.md, PRs).

## Decisions

Your `decisions.md` holds the whole stack's decisions. Starbase writes each section's gate decisions under its `## Section: <name>` heading, in the plan's order, numbered on in your ticket (`ORBIT-512.D7`), and keeps one `## Not doing` at the end that also takes each section's own list. Your own rows about a section go under its heading, in the usual shape with `<!-- foreman -->` (SKILL.md, Records); rows about the whole stack go in the main table.
