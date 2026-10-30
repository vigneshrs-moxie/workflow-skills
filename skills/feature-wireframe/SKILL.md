---
name: feature-wireframe
description: The Screens stage of a /feature job. Draws the spec's screens with the wireframe skill in its job mode and writes wireframes.html, wireframes.json and wireframes.brief.md to the job's private folder for the Foreman and Starbase. Use inside a /feature job, or when the user names a feature job's slug and asks for its screens; for screens outside a job, use the wireframe skill directly.
argument-hint: "<feature slug | spec path> [low-fi]"
---

# Feature screens (job mode of `wireframe`)

This skill is a thin wrapper: the drawing rules, the page and the build script live in the **`wireframe`** skill, a sibling of this one (`~/.claude/skills/wireframe` when installed). Read its `SKILL.md` and follow it with the job-mode rules here; where it says `<skill>`, that is the `wireframe` folder.

Input: $ARGUMENTS

## Job mode

- The input is a feature slug with a folder at `~/.claude/feature-work/<slug>/` (or `$STARBASE_FEATURES_DIR/<slug>/`, which an older copy of Starbase calls `$WORKSHOP_FEATURES_DIR`), a spec path inside one, or the Foreman says which job it's for.
- Read `spec.md` (or the spec path in `workflow-status.md`) and `options.json` if present. Don't edit the spec, `status.json`, `workflow-status.md` or briefs; the Foreman owns them. `<scratchpad>` is your own scratch folder (the worker's, or `<job folder>/scratch/` if you have none).
- **Don't ask the user questions.** Assume, and list every assumption and open decision under "Questions to settle"; the Foreman briefs them.
- Fidelity: hi-fi when the repository has a design system (the `wireframe` skill's step 3 captures it once and caches it), lo-fi when `options.json` says `"wireframes": "low"` or the user said low-fi.
- **Title:** the job's title from `options.json` (`title`), else the spec's heading. Keep it on every rebuild: the title sets the page's slug, its revision counter and where notes attach.
- Build **from the application checkout**, with the full command:
  ```bash
  # Python 3 (python3, or py -3 on Windows)
  cd <checkout> && python3 ~/.claude/skills/wireframe/build.py --title "<job title>" --sections <scratchpad>/sections.html \
    --sources <scratchpad>/sources.txt [--theme ~/.claude/wireframes/<repo>/theme.css --fonts "…" | --preset …] --job <slug>
  ```
  Use `--draft` while you check the page (nothing bumps); the build without it is the version. It writes to the job folder:
  - `wireframes.html`: the page as a complete document, viewable from disk;
  - `wireframes.json`: screens (with states and exits), choices, questions, tier, `version` and the artifact URL if one was ever published;
  - `wireframes.brief.md`: the build brief for the planner and implementer.
  A job folder that already holds `wireframes.*` means this is a revision: keep its keys and the version continues.
- **As the `feature-wireframer` worker** (the Foreman dispatched you): don't publish; Starbase shows `wireframes.html` from disk. Skip the publish and `--record-url` parts of the `wireframe` skill's step 6, and ignore the `artifact:` line the build prints.
- End with the step 6 report so the Foreman can brief it, including the `status.json` artifact entry `{ "name": "Wireframes", "path": "wireframes.html", "version": "<n>" }`.
- Feedback reaches you through the Foreman, as lines in the human's reply (`Pick A for c-entry`, `s-list: looks good | question: … | needs change: …`, or the page's Copy feedback text), not from the page. Apply them per the `wireframe` skill's step 7, keep every other key, and rebuild with the same title and `--job`; the version bumps on its own. Say what changed for the spec in your report.

## Inside Starbase

Starbase shows `wireframes.html` in an iframe (its Screens tab and the wireframe gate card), served from an origin of its own, not Starbase's, so the page's script can't reach Starbase; everything between them goes through `postMessage`. The page notices it has no artifact database (`window.claude` is absent) and:
- saves verdicts, picks, notes and the next-round intent to the browser's `localStorage` under the page's title and version (`wf-<repo>-<slug>-notes:v<n>`), so a new version starts clean and an old one keeps its notes;
- keeps **Copy feedback** working; its text is what the human pastes into the gate card's reply;
- when inside an iframe, posts to its parent on load, when the current section changes, and after a verdict or pick:
  `{ type: "wireframes", version, current: <key>, screens: [{ key, name, kind, status, choice }] }`, where `kind` is `screen`, `choice`, `questions` or `overview`, `status` is `good`, `ask`, `fix` or `""`, and `choice` is `A`, `B` or `""`;
- listens for `{ type: "wireframes-goto", key }` (scroll to that section) and `{ type: "wireframes-feedback" }` (replies to the sender with `{ type: "wireframes-feedback", version, text }`, the Copy feedback text);
- posts `{ type: "wireframes-escape" }` when `Esc` is pressed outside a notes box (Starbase puts the keyboard back on its own bar; in a notes box `Esc` only leaves the box, and nothing is posted).

A published artifact behaves as before: the database holds the notes and the page posts nothing.
