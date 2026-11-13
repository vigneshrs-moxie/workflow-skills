# Notes and PR comments: what comes in, what you answer

Shared by the `/feature` and `/bugfix` conductors. Starbase reads the two answer blocks below from the end of your reply and shows each line on the job page, so their lines are exact.

**Where the block goes.** Starbase reads only your last message that has text. So the block goes in your final message, after your last tool call: write `briefs/`, `status.json` and anything else first, then send the brief (or your answer) with the block at its end, and write nothing after it. A block followed by a tool call and a "Saved." is lost.

**How it is written:** copy the fence lines character for character, one item per line, plain text (not inside a code block), and nothing after the last `--- End ---`. The separator is a space, a middle dot `·`, a space. A reply carries each block at most once; when it has both, the comments block comes first.

## Notes from the page

The human points at places on the job page (a plan step, a spec line, a diff line, a finding, a check, a paragraph of your message, a decision, a spot on a picture) and sends the notes together. They arrive as a block, followed by any words he typed, which are a note on the whole message:

```
--- Notes (3) ---
1. [change] Plan v2 · step 4 "Add the filter to the table"
   > the words he pointed at, at most 300 characters
   Note: use the existing badge
2. [drop] Spec v3 · acceptance line 6
   > …
3. [pin] Recording 0:14 · pin 1 at 62% across, 18% down
   Note: the Apply button sits on top of the table
--- End of notes ---
```

Each note is the kind, the place (the document and the version he looked at, then the step, line or heading), the words he pointed at after `>` when there are any, and his note after `Note:`.

- **change**: make the change his note asks for, at that place.
- **drop**: take that thing out of scope or out of the document. No note needed.
- **explain**: answer in words and change nothing. Still listed in the answer block (below), and its line carries the answer itself: Starbase shows it beside the place he pointed at.
- **pin**: a spot on a picture: a recording and its time, a screen, or an image he pasted. The position is from the picture's top left corner: `62% across, 18% down`. Open the picture and look there before you change anything. When you can't open it, work from his note and say so in the answer.

A note on an older version than the latest: find the same place in the latest version. Gone from it: the note is `not done`, saying so.

The block can come alone, with a Send back, or with a go. With a Send back, the notes are the changes: make them (the same worker, or a new dispatch with the notes verbatim), review and brief again as usual. With a go, the notes are part of that go: make them, then carry on as the go says. A note that would change what was approved in a way the go can't cover (a new risk, a level trigger, a product question) is not done: say why and ask.

Answer every note, in the order and with the numbers he gave, at the very end of your final message, after the brief:

```
--- Notes answered ---
1. done · Plan v3 · step 4 removed
2. done · commit abc1234 · EmployeesTable.tsx
3. not done · the badge component has no small size
--- End ---
```

- `<n>. done · <where> · <what>`: `<where>` is where he can see the change, either the document and its new version, named as his Notes block names it (`Plan v3`, `Spec v4`, `Acceptance v2`, `Diagnosis v2`), or `commit <short sha>`; `<where>` has no `·` in it. `<what>` is what changed, in a few words (`step 4 removed`, a file name).
- `<n>. done · explained · <the answer>` for an `explain` note: the answer in one or two sentences.
- `<n>. not done · <why>`: one honest line (`needs your answer: keep the old export or drop it?`, `step 4 is no longer in Plan v3`).

One line per note, and as many lines as the `(n)` in his block.

## PR comments

He asks you to work on review comments in one of three ways: Starbase's **Fix these** (a prepared message quoting each comment he ticked, with its id, file, line and words), his own words ("look at the latest comments on the PR and make the changes"), or Starbase's review-round message (it names `review/rounds/round-<n>.md`; follow `~/.claude/skills/ship/review-rounds.md` for that one, and end with the block below too, listing the round's comments he included; a comment he left out, a failed check or a sync gets no line. The round's `status.json` items carry the same commits and replies: keep the two the same).

**Read them**, read only, from the PR the message names or else the job's open PR (`status.json` `prs`). With Fix these, the message has what you need; read GitHub only for a comment's surroundings. When he asks in words, read all three kinds:

- line comments: `gh api --paginate repos/<org repo>/pulls/<n>/comments --jq '.[] | {id, path, line, original_line, in_reply_to_id, user: .user.login, created_at, body}'`
- reviews, for a review's own text: `gh api --paginate repos/<org repo>/pulls/<n>/reviews --jq '.[] | {id, state, user: .user.login, submitted_at, body}'`
- conversation comments: `gh api --paginate repos/<org repo>/issues/<n>/comments --jq '.[] | {id, user: .user.login, created_at, body}'`
- the PR's author: `gh api repos/<org repo>/pulls/<n> --jq .user.login`

Write them as shown, with nothing added but the usual `cd <folder> && ` in front (no `--method`): Starbase lets these run without a click, in an Auto job too. An outdated line comment has `line: null`; its line is `original_line`.

Work on every comment not answered yet, his own and ones from before Starbase first looked included:

- **A line-comment thread** is one item, under its first comment's id (the one with no `in_reply_to_id`). It is answered when the PR's author replied in it after the reviewer's last comment; a reviewer's later reply opens it again.
- **A review's text**: only a `CHANGES_REQUESTED` or `COMMENTED` review with a body. Skip `APPROVED` and `DISMISSED` reviews and empty bodies. It is answered when the PR's author wrote a conversation comment after it.
- **A conversation comment** is answered when the PR's author wrote a conversation comment after it.
- Any comment whose id already has a line in an earlier `--- Comments answered ---` block of this job, or an item in its `review/rounds` files, is answered.
- Leave out bots' summaries and empty comments. When you are not sure, list it and say above the block that it may already be answered.

The id is `c<id>` for a line comment (a thread: its first comment's id), `r<id>` for a review's text and `i<id>` for a conversation comment, the GitHub id after the letter. Use the id exactly as Starbase's message gives it. A message that gives only the comment's GitHub link: `#discussion_r901` is `c901`, `#pullrequestreview-55` is `r55`, `#issuecomment-77` is `i77`.

**Fix them** on the job's branch in its worktree (the fork branch, never the org branch, never a rebase): one commit per comment, its message naming the comment, `fix(api): name the id feedbackId (review comment c901 on api.ts:40)`. When two comments ask for the same change, one commit answers both. Then run the job's checks (Orbit: `cd app && npm run check`) and the tests the changes touch, and say what ran in one line above the block. A comment that asks for a product decision, or for a change the approved plan or diagnosis doesn't cover (migrations, auth, roles, office visibility, secrets, integrations), is left with the reason, and you ask him above the block.

**Don't push, and don't reply, resolve or ask for a review on GitHub.** Starbase pushes, and posts or copies each reply, on his click. A push he asks for afterwards in words is a push like any other, with its own yes; for a change asked on PR #2 it goes through a follow-up PR #1 (`review-rounds.md`, What travels where).

**Answer** with a short summary, then the block, one line per comment, in the order of his message (when he asked in words, the order you read them):

```
--- Comments answered ---
c901 · fixed in a1b2c3d · reply: Fixed in a1b2c3d: renamed to `feedbackId`.
i77 · answered · reply: It's only called from the job page, so the extra query runs once per page load.
c903 · left · the helper is shared with the Jobs list · reply: Kept as it is: the helper is shared with the Jobs list, so renaming it here would touch both. Happy to do it in a follow-up.
--- End ---
```

- `<id> · fixed in <short sha> · reply: <reply>`: the one commit that fixed it, as `git log --format=%h` prints it.
- `<id> · answered · reply: <reply>`: a question answered with no change.
- `<id> · left · <why> · reply: <reply>`: kept as it is; `<why>` is a few words with no `·` in it.

Every line has a reply: one paragraph on one line, written to the person who commented, in the reply style of `~/.claude/skills/ship/review-rounds.md` (short, polite, specific; what changed and where, or why not; no "Great catch!", no apology, no restating the comment). He edits it, then posts it or copies it. A message that only asks what a comment means ("What is he asking?") is answered in words: no change and no block.
