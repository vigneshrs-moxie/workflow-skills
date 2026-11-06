---
name: review-walkthrough
description: Build an in-person review walkthrough page for the current branch or a PR and publish it as a private artifact. It sorts every change into four zoom levels (System, Module, Function, Line) and has a view picker. Quick shows a one-line summary plus only the highest level that has changes, in plain English, with "Explain ›" jumps to a fuller before/now explanation. All shows every level; each level can also be viewed alone. Each section has a verdict and notes, plus a file list and a wrap-up that collects follow-ups. Use when the user asks for a review walkthrough, a review doc, a code review support page, or "prep this for review".
---

# Review walkthrough

A one-page **cue sheet** for an in-person review. The user talks; the page gives them something to talk from and somewhere to record the outcome.

Most reviews are short: the user and a reviewer (often Raj, ~30 minutes, 2–3 PRs) look at the big decisions, and the reviewer suggests changes. So the page opens in **Quick** mode: one sentence on what the PR does for users, then only the **highest zoom level that has changes**. A PR that adds a table opens on System. A UI tweak has nothing at System or Module, so Quick drops to Function or Line by itself. **All** shows every level, top down, and each level button (System, Module, Function, Line) shows just that level with the summary. `M` switches Quick and All.

Every System and Module item carries a short **explanation** (before, now, and what it connects to) for when the reviewer asks "tell me more". Quick hides it and shows **Explain ›** instead, which switches to All, opens the explanation and scrolls to it.

`template.html` holds all styling and behavior and `build.py` fills it from git. You write only the `<section>` blocks. The page already provides:
- **Header:** title, branch, SHA and PR; **view picker** (Quick · All · System · Module · Function · Line, with empty levels disabled); **Diff** button; **Files** dropdown with +/− counts and GitHub links; **A+** for a TV; **Copy follow-ups**.
- **Section strip** with a status dot per section and an "x/y reviewed" count for the sections in the current mode.
- **Pointers:** each bullet in `ul.points` gets a tick box.
- **Per section:** verdict buttons (Looks good / Question / Needs change) and a notes box.
- **Quick note:** when the top level isn't System, Quick says which levels were empty.
- **Wrap-up:** a tally, every question, change request and note (from both modes, and from section keys an earlier version of the page had), and a legend of the four levels.
- **Keys:** `M` Quick/All, `J`/`K` next/previous section, `1` `2` `3` verdict, `N` notes, `Esc` leave notes.

Verdicts, ticks and notes save to the artifact's database by section key, so republishing keeps them.

Be fast. Don't ask questions unless the base branch can't be worked out. Don't run tests, typechecks or linters. Report only what this session, the PR or the history shows, and say plainly what hasn't been run.

## The four zoom levels

These are distances from the code, not kinds of change. Every change goes at the **highest** level where it matters. Sort by the first test that answers yes.

| # | Name | What counts | Test |
|---|---|---|---|
| 1 | **System** | Changes to how the app is put together: a new table or data model, a new service or integration, a new family of endpoints or a new capability (bulk updates, export, background job), logic moved between frontend and backend or between services, a new auth or permission model, a deploy-order constraint, a new pattern other code must now follow. | Would it change the diagram of the whole app? |
| 2 | **Module** | Design inside the existing architecture: a new module or component, responsibilities moved between files, a new shared helper used across layers, a changed request or response shape, a new status or field threaded through every layer, a deliberate boundary (e.g. logic kept out of browser-callable code). | Would it change the diagram of this one feature? |
| 3 | **Function** | How the main pieces work: the main flows, the rules a function enforces (what's copied, when emails go out), state handling, transaction and concurrency choices, caps and limits. | Would you explain it with the function open on screen? |
| 4 | **Line** | Guards, edge cases, error handling, race fixes, browser quirks, styling, copy tweaks, comments, tests. | Does it only matter to someone reading that line? |

Be strict about Levels 1 and 2. Most PRs have **nothing** at System. A new button, column, dialog, filter or wording change is never System or Module on its own; it's Function or Line. Don't promote a change to fill a level. Empty is the right answer, and it's what makes Quick honest.

## 1. Gather the facts (in parallel)

- **Base:** `moxie/main` in moxie-portal, otherwise `upstream/main` or `origin/main`. Use the merge-base. Don't fetch without asking. A PR into `staging` still diffs against main's merge-base, because staging diverges.
- **For a PR link:** `gh pr view <n> --repo OWNER/REPO --json title,body,headRefName,headRefOid,baseRefName,commits` and `gh pr checks`. If the head isn't local, find a worktree or remote branch with the feature (`git worktree list`, `git branch -r`), and confirm with `gh api repos/OWNER/REPO/compare/<local>...<head>` that the remaining commits change no files.
- `git log --oneline <mb>..HEAD`, `git diff --stat <mb>..HEAD`, then read `git diff <mb>..HEAD` file by file. Skip lockfiles and generated files. Save large diffs to the scratchpad and read them.
- The PR body and this conversation: why it was made, decisions, known limits, check results.
- Note **real problems** for "Fix before merge": stale comments, leftover debug code, removed lint suppressions, risky migrations, missing null handling, migration-order traps.

## 2. Build the level map (before writing anything)

Write `<scratchpad>/levels.md`: under each of the four levels, every change at that level in one line. Read the diff for this; the PR body says what was meant, the diff says what happened. Then:
- Find the **top level**: the highest level with anything in it. That's what Quick will show.
- For each System or Module item, note the decision, any real alternative it rejected, how this part worked before, and what code around it calls it or is affected by it. These become its explanation.
- Check nothing is promoted: re-run the tests above on every Level 1 and 2 line.

## 3. Write the sections

Write them to `<scratchpad>/sections.html` in this order. **Leave out any level section that is empty.** The top level is shown in Quick automatically; the build needs no flag.

| key | attrs | step label | h2 | contents |
|---|---|---|---|---|
| `overview` | `data-quick` | Summary | What this does | One `<p class="lede">`: what the PR does for users, one sentence, plain English. Nothing else. |
| `try` | | Show it | Demo | `.try` with 3–5 steps: page, role, click, what you see. Only if something is user-facing. |
| `system` | `data-level="1"` | Level 1 · System | System changes | `ul.points`, each item with a `details.explain` |
| `module` | `data-level="2"` | Level 2 · Module | Module changes | `ul.points`, each item with a `details.explain`; optionally grouped with `<h3>` Frontend / Backend / Data / Shared |
| `function` | `data-level="3"` | Level 3 · Function | How it works | `<h3>` per mechanism, 1–4 pointers each |
| `line` | `data-level="4"` | Level 4 · Line | Fine print | `ul.points`; last pointer summarises the tests |
| `decide` | | For discussion | Questions to settle | `ul.points`, each starting `<span class="flag">Decide</span>` |
| `ship` | | Ship it | Ship it | Migration (+ rollback), risk, "Fix before merge" with `<span class="flag">Fix</span>` (or "nothing found"), Checks, Review, Next. |

### Writing the top level (shown in Quick)

Whichever level is the top one, write it as **plain sentences**, because it's read aloud to someone who may not open the code.
- One or two sentences per item, about 15–40 words. **Say the decision, then why it matters.** Name the rejected alternative when there was a real one: "…instead of living inside the single-ticket endpoint."
- At most five items. Merge related ones.
- Plain words. Name tables, endpoints or modules only when the name itself helps, and gloss it ("a new status-history table"). No function names, no file names.
- File chips are allowed at the end of an item; Quick hides them.

### Writing explanations (System and Module items)

Every System and Module item ends with an explanation, collapsed by default. It's for when the reviewer wants more than the one-liner but not the code: summarised detail with the context of the code before and around it.

```html
<details class="explain"><summary>More detail</summary><dl>
  <dt>Before</dt><dd>How this part worked before the PR, or that it didn't exist.</dd>
  <dt>Now</dt><dd>What it does now, in two or three sentences.</dd>
  <dt>Around it</dt><dd>What calls it, what it calls, and what else it affects.</dd>
  <dt>Why</dt><dd>Why this way; the alternative it beat. Leave out if there was no real choice.</dd>
</dl></details>
```

- One to three plain sentences per row. Describe code in words ("the single-ticket endpoint", "the Feedback page's data loader"). Name a module only with a gloss. No code, no line numbers.
- Put the `details.explain` inside the `<li>`, after the item text and any file chip.

### Writing the levels below the top

These are cues for a code review.
- **Each pointer is a cue, not an explanation.** About 4–12 words, fragments are fine, nouns first. Example: `<strong>Submit</strong> disabled until every 1 has a comment`.
- One idea per pointer. No "because" clauses; the user says those out loud.
- Bold the first word or two when it names the thing.
- Put a file chip inline at the end of the pointer it supports.
- A `<pre>` of 1–3 lines only when a signature says it faster than words.

### Section shape

`data-key` is stable; keep the same keys on republish.

```html
  <section data-key="overview" data-quick>
    <div class="content">
      <p class="step">Summary</p>
      <h2>What this does</h2>
      <p class="lede">Admins can create a Role Template by copying an existing one.</p>
    </div>
    <aside><textarea id="n-overview" aria-label="Notes" placeholder="Notes"></textarea></aside>
  </section>

  <section data-key="module" data-level="2">
    <div class="content">
      <p class="step">Level 2 · Module</p>
      <h2>Module changes</h2>
      <ul class="points">
        <li><strong>The copy logic lives in its own module</strong> that the browser can't call. Only the admin action calls it, after the admin check, instead of the copy sitting in the server-actions file where every export is callable. <span class="files"><a href="{{BLOB}}/app/src/lib/role-templates/copy.ts#L29" data-file="app/src/lib/role-templates/copy.ts" data-line="29"><code>copy.ts</code></a></span></li>
      </ul>
    </div>
    <aside><textarea id="n-module" aria-label="Notes" placeholder="Notes"></textarea></aside>
  </section>
```

Other blocks:

```html
<div class="try"><h4>Try it</h4><ol><li>…</li></ol></div>
<div class="compare"><div><h4>Before</h4><ul><li>…</li></ul></div><div><h4>Now</h4><ul><li>…</li></ul></div></div>
<details class="more"><summary>Show code</summary><pre><code>…</code></pre></details>
```

**File chips:** use `{{BLOB}}/path#L<n>` with `data-file` and `data-line`; `build.py` fills in the repository and head commit. Add `data-line` and `#L` only for lines confirmed with `grep -n` (on `git show <sha>:<path>` when the code isn't checked out). If the commit isn't pushed, use `<code data-file="…">` with no link. Escape `<`, `>` and `&` in code.

## 4. Build and publish

Run from the checkout or worktree that holds the feature:

```bash
# Python 3 (python3, or py -3 on Windows)
cd <worktree> && python3 ~/.claude/skills/review-walkthrough/build.py --title "Short feature name" --sections <scratchpad>/sections.html [--pr <url>] [--mode full]
```

- `--pr` makes the header, Diff button and all links point at that PR's repository and head commit. Use it whenever reviewing a PR, especially from a fork checkout.
- `--mode` sets the mode the page first opens in. Default `quick`. Use `full` only when the user says the review is a code review.

The script writes `~/.claude/review-walkthroughs/<repo>/<branch>.html` and prints the existing artifact URL, if this branch has one.

- **Existing URL, published earlier in this conversation:** publish the same file path again. **From an earlier conversation:** read it (`action: "read"`) first, then publish with that `url`. Either way leave out `icon` and `capabilities`.
- **New:** load the `artifact-capabilities` skill. Publish with `icon: "review"`, a one-sentence `description` and `capabilities: {"db": {}, "user": {}}`. Then write the URL into the `.url` file the script named.
- Reply with the link, which level Quick opens on, and the "Fix before merge" items, one line each. Don't repeat the rest of the page.
