# Review rounds: the steps, the reply style, examples

A **round** is everything one reviewer asked for in one go: a "Request changes" review and its comments (or two comments or more within ten minutes of each other), plus the checks that failed on the same commit. The dashboard keeps each round in the job folder as `review/rounds/round-<n>.md` (and `.json`, its own record); each item there has an id (`c901` a line comment, `r55` a review's own text, `i77` a conversation comment, `k:lint@a1b2c3d` a failed check, `sync:staging` bringing in the base). Use those ids in `status.json`.

## The steps

1. **Read the round** (`round-<n>.md`, or the PR on GitHub, read only). Items the human left out are listed as such: don't work on them.
2. **Plan, before any change.** Per item: its kind and what you will do. Write it to `status.json` and stop to show it only if the human asked to see the plan first; otherwise carry on.
   - **change**: asks for a code change. **question**: asks something and wants an answer. **nit**: small and optional (still answered). **check**: a failed check (fix it; it gets no reply).
   - plan **fix**, **answer** or **wont_change** (with the reason, short and honest).
3. **Fix**, on the fork branch in the job's worktree: one commit per item or per small group, each message naming the comment (`fix(api): name the id feedbackId (review comment on api.ts:40)`). Never on another branch, never a rebase once the branch is on the fork.
4. **Check**: the profile's checks (Orbit: `cd app && npm run check`) and the tests the change touches. One line on what ran, in the round's `checks`: "npm run check and 41 tests passed on your branch."
5. **Draft the replies**, one per comment (below), and set the round to `ready`.
6. **Stop.** Don't push, don't reply on GitHub, don't resolve, don't ask for a review, don't merge. The dashboard's Send back does those on the human's go; from the terminal, each needs its own yes.

## status.json `prs[<n>].rounds`

```json
{
  "number": 2, "state": "changes_requested",
  "rounds": [{
    "round": 1, "state": "fixing",
    "doing": "Renaming the id in api.ts", "next": "The empty state question",
    "checks": "npm run check and 41 tests passed on your branch.",
    "items": [
      { "id": "c901", "kind": "change", "plan": "fix", "plan_text": "Rename to feedbackId everywhere", "state": "fixed", "commit": "a1b2c3d", "reply": "Fixed in a1b2c3d: renamed to `feedbackId`." },
      { "id": "c902", "kind": "question", "plan": "answer", "state": "answered", "reply": "It shows the empty state: there is no saved filter yet, so the list is the full one." },
      { "id": "c903", "kind": "nit", "plan": "wont_change", "state": "wont_change", "reason": "The helper is shared with the Jobs list", "reply": "Kept as it is: the helper is shared with the Jobs list, so renaming it here would touch both. Happy to do it in a follow-up." },
      { "id": "k:lint@a1b2c3d", "kind": "check", "plan": "fix", "state": "fixed", "commit": "b2c3d4e" }
    ]
  }]
}
```

States: the round `planning` → `fixing` → `ready`; each item `todo` → `working` → `fixed` (with `commit`), `answered` or `wont_change` (with `reason`). Write the whole file each time, as always.

## The reply style

Short, polite, specific. One reply per comment, written to the person who asked, in the PR's language. Say what changed and where, or why not. No "Great catch!", no apologising, no restating the comment.

- **Fixed:** "Fixed in a1b2c3d: renamed to `feedbackId`." / "Fixed in b2c3d4e: the empty list now shows "No feedback yet" instead of a blank table."
- **Several commits:** "Fixed in a1b2c3d and c3d4e5f: moved the check into the route and added a test for the 404."
- **Answered:** "It's only called from the job page, so the extra query runs once per page load. I've added a comment saying so (c3d4e5f)."
- **Won't change:** "Kept as it is: `useMemo` here would cache across tenants. Happy to revisit if you see it differently."
- **A nit taken:** "Done in d4e5f6a."
- **Outdated comment** (the line has changed since): answer what was asked, and say where it is now: "Fixed in a1b2c3d (the code moved to `lib/feedback.ts:12`)."

## What travels where (Orbit)

- A change asked for on **PR #2** (Raj's): commit on the fork branch → push to your fork → **follow-up PR #1**, fork → the moxie branch (`pr-body.md` "Follow-up PR #1") → merged (you review and merge PR #1) → PR #2 shows the new commits → replies → resolve the Fixed comments → Raj asked again.
- A change asked for on **PR #1**: push, and PR #1 has it; no follow-up.
- **A check fails after the push**: the same loop with its log; the fix is pushed the same way.
- **The base moved** (PR #2 conflicts with staging): the Sync procedure in `SKILL.md` (merge staging in, never rebase), then the same Send back.
- **A question only**: the reply and the review request; nothing is pushed and no PR is opened.
- **The approval was dismissed by the push** (some repos drop approvals on new commits): Raj is asked again; nothing else to do.
