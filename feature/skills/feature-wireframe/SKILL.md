---
name: feature-wireframe
description: The Screens stage of a /feature job. Draws the spec's screens with the wireframe skill in its job mode and writes wireframes.html, wireframes.json and wireframes.brief.md to the job's private folder for the Foreman and Starbase. Use inside a /feature job, or when the user names a feature job's slug and asks for its screens; for screens outside a job, use the wireframe skill directly.
argument-hint: "<feature slug | spec path>"
---

# Feature screens (job mode of `wireframe`)

This skill is a thin wrapper: the drawing rules, the page and the build script live in the **`wireframe`** skill, a sibling of this one (`~/.claude/skills/wireframe` when installed). Read its `SKILL.md` and follow it with the job-mode rules here; where it says `<skill>`, that is the `wireframe` folder.

Input: $ARGUMENTS

## Job mode

- The input is a feature slug with a folder at `~/.claude/feature-work/<slug>/` (or `$STARBASE_FEATURES_DIR/<slug>/`), a spec path inside one, or the Foreman says which job it's for.
- Read `spec.md` (or the spec path in `workflow-status.md`) and `options.json` if present. Don't edit the spec, `status.json`, `workflow-status.md` or briefs; the Foreman owns them. `<scratchpad>` is your own scratch folder (the worker's, or `<job folder>/scratch/` if you have none).
- **Don't ask the user questions.** Assume, and list every assumption and open decision under "Questions to settle"; the Foreman briefs them.
- **The page is one prototype:** an Info tab, then one phone or laptop the reviewer clicks through in place, with pinned notes. The `wireframe` skill's `reference/prototype.md` sets its shape, in place of its step 5 and section shapes. A job has no text tier, sketch, lo-fi or review page, no panel per screen and no long explanation beside a screen. What a reviewer needs to know goes on the Info tab in a few lines. Each real design choice is a decision on the Info tab, with your recommended option the one the prototype shows.
- **Laptop and phone.** Draw laptop screens always. When the spec has people using the feature on a phone, draw phone screens too, designed for the phone (`reference/prototype.md`, "Designing phone screens": one job per screen, a summary then the list, details one tap away, little colour, no tile grids), never the laptop screen squeezed. In a job this replaces the "Laptop first" line of `reference/prototype.md`.
- **Title:** the job's title from `options.json` (`title`), else the spec's heading. Keep it on every rebuild: the title sets the page's slug, its revision counter and where notes attach.
- Build **from the application checkout**, with the full command:
  ```bash
  # Python 3 (python3, or py -3 on Windows)
  cd <checkout> && python3 ~/.claude/skills/wireframe/build.py --title "<job title>" --sections <scratchpad>/sections.html \
    --sources <scratchpad>/sources.txt [--theme ~/.claude/wireframes/<repo>/theme.css --fonts "…"] --job <slug>
  ```
  Always pass `--job <slug>`, which makes the prototype page; never pass `--fidelity`. Pass `--theme` when the repository has a design system (the `wireframe` skill's step 3 captures it once and caches it). With none, pass no theme: the build prints `no --theme or --preset: a job's prototype uses the bundled admin preset`, and your summary says the screens use the bundled look, not the app's. When the spec has FR ids, write its rows to `<job folder>/fr-table.md`, one `| FR-001 | <requirement> |` line each, leaving out removed rows, and add `--requirements <job folder>/fr-table.md`: the page then shows the same ids ops hear in the meeting. With no FR ids, take Requirements from the spec's acceptance lines. Add `--start-device phone` when the phone is where the feature is mostly used, and `--pack` when the Foreman asks for the stakeholder PDF (`wireframes.pack.pdf`).
  Use `--draft` while you check the page (nothing bumps); the build without it is the version. It writes to the job folder:
  - `wireframes.html`: the page as a complete document, viewable from disk;
  - `wireframes.json`: screens (with states and exits), choices, questions, tier, `version` and the artifact URL if one was ever published;
  - `wireframes.brief.md`: the build brief for the planner and implementer.
  A job folder that already holds `wireframes.*` means this is a revision: keep its keys and the version continues.
- **An older screens source.** When the build stops with `This job's screens source is in the older review-page format. A job's screens are always the prototype page: write the source again as a prototype (reference/prototype.md), then build.`, write a new prototype source from the spec and the latest feedback. Don't convert or reuse the old one.
- **As the `feature-wireframer` worker** (the Foreman dispatched you): don't publish; Starbase shows `wireframes.html` from disk. Putting the page on the prototypes site is the human's **Publish** button on the job's Screens tab, not your step, so never run `publish.py`. Skip the publish and `--record-url` parts of the `wireframe` skill's step 6, and ignore the `artifact:` line the build prints.
- End with the step 6 report so the Foreman can brief it, including the `status.json` artifact entry `{ "name": "Wireframes", "path": "wireframes.html", "version": "<n>" }`.
- Feedback reaches you through the Foreman, not from the page: the page's Copy feedback text pasted in the human's reply, what the human's **Pull notes** button brought from the site, or lines they typed in the same form. Reviewers pin notes on screens (kinds `change`, `question`, `idea`) and pick decisions; each is one line:
  - `Pick A for c-nav`, or `Pick A for c-nav (why: Less on the page.)`;
  - `s-<screen id> (<device>, at "<pin label>"): <needs change | question | idea>: <text>`, such as `s-needs (phone, at "Theo Brandt"): needs change: …`. `at` comes only with a pin; Copy feedback adds the View as role when the page has roles, and Pull notes adds `on r<n>` to a note left on an earlier revision.

  Apply them per the `wireframe` skill's step 7, its prototype bullet, keep every other key, and rebuild with the same title and `--job`; the version bumps on its own. Say what changed for the spec in your report.

## Inside Starbase

Starbase shows `wireframes.html` in an iframe (its Screens tab and the wireframe gate card), served from an origin of its own, not Starbase's, so the page's script can't reach Starbase; everything between them goes through `postMessage`. The page notices it has no artifact database and no site, and:
- saves notes and picks to the browser's `localStorage` under the page's title and version (`wf-<repo>-<slug>-notes:v<n>`, notes under `…:feedback`), so a new version starts clean and an old one keeps its notes;
- keeps **Copy feedback** working; its text is what the human pastes into the gate card's reply;
- posts to its parent on load, when the screen changes, and after a note or pick:
  `{ type: "wireframes", version, current, screens: [{ key, name, kind, status, choice }] }`. `current` is `s-<id>` on the Prototype tab, else `overview`. `screens` holds Info (`overview`), each decision (`kind: "choice"`, `status` `good` once picked, `choice` `A`, `B` or `""`) and each `data-pack` screen (`kind: "screen"`, `status` `fix` with a `change` note, `ask` with any other note, else `""`);
- listens for `{ type: "wireframes-goto", key }` (`overview` opens Info, `s-<id>` that screen in the prototype, `c-<key>` that decision) and `{ type: "wireframes-feedback" }` (replies to the sender with `{ type: "wireframes-feedback", version, text }`, the Copy feedback text);
- posts `{ type: "wireframes-escape" }` when `Esc` is pressed in the prototype with nothing left to close (pin mode, an overlay or a notes box closes first, and nothing is posted).

A published artifact behaves as before: the database holds the notes and the page posts nothing.
