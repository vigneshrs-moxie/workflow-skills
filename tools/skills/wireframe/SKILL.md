---
name: wireframe
description: Draw the screens for a feature or product idea and publish them as a private review page before anything is built. Four fidelities. Text, in the reply, for a fast first shape. Sketch, hand-drawn. Lo-fi, greyscale. Hi-fi in the app's own design, read from the repository, or in a bundled preset when there is no design system. One panel per screen in flow order, states as tabs, Before/Now pairs, numbered callouts, clickable exits between screens, and two side-by-side options wherever there is a real design choice. Reviewers mark verdicts, pick options and leave notes on the page; feedback is read back and the page revised in place. Hi-fi pages on their own are a prototype: an Info tab, then one phone or laptop you click through in place, like the real site. Also writes a build brief any implementer can work from. Works in any repository or with none, and inside a /feature job through the feature-wireframe wrapper. Use when the user asks for wireframes, mockups, screens, designs, a prototype, "what would this look like", or wants to see a feature before building it.
argument-hint: "<idea in a sentence | spec path> [text|sketch|lo-fi|hi-fi] [preset:admin|consumer|mono]"
---

# Wireframes

Screens for an idea, for people to review **before** anyone builds it. The page answers "is this the right thing, in the right place, with the right steps, and does it look like it belongs?"

Input: $ARGUMENTS

`template.html` holds all styling and behaviour and `build.py` fills it. Both are in this skill's folder: the base directory shown when the skill loads (`~/.claude/skills/wireframe` when installed). Below, `<skill>` means that folder. You write only the `<section>` blocks (and, for hi-fi, a theme file). The page already provides:
- **Header:** title with a **tier chip** (what this fidelity decides and what it doesn't), where it was drawn from, **Based on** (the files you read), **Screens: Light/Dark** (hi-fi), **A+**, **Copy feedback**.
- **Section strip** with a status dot per section and "x/y reviewed · x/y picked".
- **Flow:** a numbered row of every screen in the overview, and a **map** of where each screen leads.
- **Hotspots:** a control marked `data-go` jumps to the screen it opens; each screen lists its exits.
- **Per section:** Looks good / Question / Needs change and a notes box; in a design choice, **Pick A / Pick B**.
- **States** become tabs; **pins** and **callouts** light each other up on hover.
- **Hi-fi screens** are laid out at real width and scaled to fit, with a **100%** button.
- **Wrap-up:** a tally, every pick, verdict and note, a **states coverage** table, the revision number, and **Next round** (refine / adjacent / explore).
- **Keys:** `J`/`K`, `1` `2` `3` verdict, `A`/`B` pick, `N` notes, `Esc`.

Verdicts, picks, notes and the next-round intent save to the artifact's database by section key, so a revised page keeps them and you read them back (step 7). Every build also writes a **build brief** (`<slug>.brief.md`) and adds the page to the gallery at `~/.claude/wireframes/index.html`.

## Two ways this runs

**On its own** (the user runs `/wireframe` or asks for screens): ask up to three questions when you truly can't draw without the answers, build, publish, reply with the link.

**Inside a `/feature` job** (through the `feature-wireframe` skill, or the Foreman says which job it's for): read `spec.md` and `options.json` in the job folder (`~/.claude/feature-work/<slug>/` or `$STARBASE_FEATURES_DIR/<slug>/`); don't edit the spec, `status.json`, `workflow-status.md` or briefs; **ask no questions** (assume, and list every assumption and open decision under "Questions to settle"); pass `--job <slug>` so `wireframes.html`, `wireframes.json` and `wireframes.brief.md` land in the job folder; as the `feature-wireframer` worker, don't publish (Starbase shows `wireframes.html` from disk) and end with the step 6 report. Feedback then arrives as lines in the Foreman's prompt, not from the page.

Both ways produce the same page; only the questions and the extra job files differ.

## Which page

- **Hi-fi: a prototype page,** on its own or inside a `/feature` job. A short Info tab, a Prototype tab where every click happens in place, and Requirements. Read `reference/prototype.md` and use it in place of step 5 and the section shapes below. Steps 1 to 4 still apply, except that a real design choice becomes a decision you can try live rather than two frames. Screens are laptop only unless the feature is for phones.
- **Sketch or lo-fi: the review page** described in the rest of this file. Use it for hi-fi too if the user asks for side-by-side options or per-screen verdicts.

## 1. Understand the idea

- **One-line idea:** use it as given. **Spec or job:** read its goal, users, flows and acceptance criteria.
- Decide who uses it (role), where they start, and what they finish with.
- Standalone, ask at most three questions, each with your recommendation, only when you can't draw without them. Otherwise assume and list each assumption under "Questions to settle", flagged `Assumed`.

## 2. Pick the fidelity

| Tier | When | Decides | Needs |
|---|---|---|---|
| **text** | the user wants a quick shape in chat first, or the idea has several possible shapes | structure, steps, wording | nothing; see `reference/text-tier.md`, no build |
| **sketch** | early, when a finished look would be mistaken for a decision; a whiteboard for a group | structure, flow, wording | `--fidelity sketch` |
| **lo-fi** | the layout and content matter but the look isn't the question; no design system to copy | layout, content, wording | nothing (the default) |
| **hi-fi** | the repository has a design system: the screens should look built | everything a reviewer can see | `--theme` from the app (step 3) or `--preset` |

Default: **hi-fi** when the repository has a theme you can capture, **lo-fi** otherwise. The user's word wins ("sketch", "low-fi", "quick", "in chat"). Sketch and lo-fi share the same markup, so a sketch becomes a lo-fi page by rebuilding with the other flag.

## 3. Read the repository (automatic inside one)

When the working directory is a git repository, read it before drawing. **Read-only:** no servers, installs, builds, tests or database queries.
- Find the pages and components the idea touches: route folders, the sidebar or navigation definition, and the page closest to where the feature lives (grep for its title, route or a nearby label).
- Note what a reviewer would recognise: the sidebar items for the viewer's role and which is active, the page header (title, breadcrumbs, where its buttons sit), table columns, filters, how dialogs, sheets, menus, banners, toasts and empty states already look and are worded, and the role names.
- **Reuse what's there.** If the app already has a pattern for this, draw that pattern with its real wording. Never invent a new pattern where one exists. When two existing patterns would both fit, that's a design choice (step 4).
- **Example data is invented.** Plausible names, numbers and dates, never real people, customers or records from the code, fixtures or a database.
- **The request assumes something the page doesn't have** (filters, a column, a role): draw it as new, and add a `Decide` question saying it doesn't exist today. **Part of it exists already** (a menu item, a route, a half-built action): draw that part as existing, say so in the overview, and mark only what's new.
- Write every file you read to `<scratchpad>/sources.txt`, one repository-relative path per line; with a cached design, add the files its `sources:` list names, since the screens rest on them too.
- `<skill>/example/` holds a finished lo-fi page (`sections.html`) and a hi-fi one on a plain-CSS app (`hifi/`), both for a made-up billing app. Read them for the shape of the markup when unsure; never copy their feature.

**Hi-fi: capture the design once.** Run `python3 <skill>/build.py --design-check` with Python 3 (`python3`, or `py -3` on Windows). If the cache is fresh, read `~/.claude/wireframes/<repo>/design.md` and use its `theme.css` instead of re-reading the stylesheet and components. If it's stale or missing, follow `reference/design-capture.md` (recipes for Tailwind v4, Tailwind v3, plain CSS, theme objects, and none), write both files, and run `--design-stamp`. No design system: use `--preset admin|consumer|mono` and say so under Questions to settle.

## 4. Map the screens (before writing anything)

Write `<scratchpad>/screens.md`:
- **Screens in flow order.** One per distinct view: a page, a dialog, a sheet, an email. A dialog over a page is its own screen. Usually 2–6.
- **Changed screens:** Before and Now side by side.
- **States** per screen, from this list, only those that differ visibly and matter: empty, loading, error, success, no permission, a long list or long names, phone width. One to three per screen. Say under Questions to settle which you left out and why ("Loading not drawn: the list loads in one request").
- **Exits:** what leaves each screen and where it goes. Every screen has one unless the flow ends there. No dead ends.
- **Awkward data:** every list shows a name that overflows, a zero and a 99+ count, or an empty case. Tidy fake data hides what real data breaks.
- **Design choices: two options, side by side**, wherever there's a real choice a reviewer would want to make: where an entry point lives, a dialog or a separate page, single or bulk, inline edit or form. At most three per page. Mark your recommended option and say why in one line. A choice nobody would argue about is a decision, noted in a callout. If there's no real choice, say so in the overview.
- **Callouts:** the decisions a reviewer should notice: who sees it, when a control is disabled, what is copied or sent, limits, what happens next. Three to six per screen.

## 5. Write the sections

Write them to `<scratchpad>/sections.html` in this order:

| key | attrs | step label | h2 | contents |
|---|---|---|---|---|
| `overview` | | Summary | What this adds | `<p class="lede">`: what the feature lets someone do, one plain sentence. A line on who uses it and where it starts. `<ol class="flow" id="flow"></ol>` (filled automatically, the map goes under it). The legend. |
| `s-<name>` | `data-screen="Short name"`, `data-end` on the last screen | leave empty: filled as "Screen n" | the screen's name | One line of context, the screen (or `.states`, or `.pair`), then `ol.callouts`. |
| `c-<name>` | `data-choice` | Design choice | the question, e.g. "Where does the export start?" | One line of context, then `.options` with exactly two `figure.option`. |
| `questions` | | Before building | Questions to settle | `ul.points`; each item starts `<span class="flag">Decide</span>` or `<span class="flag assume">Assumed</span>`. |

Put each design choice right after the screen it belongs to. Keys are stable: keep them when you revise, so the user's notes stay attached.

The overview's legend, as is:

```html
<div class="legend"><span><i class="sw"></i>New in this feature</span><span><i class="sw gone"></i>Removed</span><span><i class="pin">1</i>See the note with that number</span></div>
```

### Section shapes

```html
  <section data-key="s-list" data-screen="Employees list">
    <div class="content">
      <p class="step"></p>
      <h2>Employees list</h2>
      <p>Admins start here. The new button sits with the page's other actions.</p>
      <div class="frame hifi" data-url="/admin/employees" data-width="1280">… <span class="…" data-go="s-export">Export</span> …</div>
      <ol class="callouts">
        <li><strong>Only admins</strong> see Export; other roles see the page as it is today.</li>
      </ol>
    </div>
  </section>
```

**Hotspots:** `data-go="<section key>"` on the control that leaves a screen (a button, a row, a menu item, a link). The build errors on a target that doesn't exist and warns on a screen with no exit; the last screen gets `data-end` on its section. When the control's text isn't a good label ("→", an icon), add `data-go-label="the downloaded file"`.

States, as tabs: `<div class="states">` holding `<figure class="state" data-label="Default">` … one frame each.
Before and Now: `<div class="pair">` holding two `<figure>`, each with `<figcaption>Before</figcaption>` (or Now) and a frame.

A design choice:

```html
  <section data-key="c-entry" data-choice>
    <div class="content">
      <p class="step">Design choice</p>
      <h2>Where does the export start?</h2>
      <p>Both use patterns the app already has.</p>
      <div class="options">
        <figure class="option" data-option="A" data-label="Button in the page header">
          <div class="opt-head"><h4><b>A</b>Button in the page header</h4><span class="rec">Recommended</span></div>
          <div class="frame hifi" data-url="/admin/employees" data-width="1280">…</div>
          <div class="tradeoffs"><div><h5>Good</h5><ul><li>One click, always visible</li></ul></div><div><h5>Watch</h5><ul><li>Header gets a third button</li></ul></div></div>
        </figure>
        <figure class="option" data-option="B" data-label="Item in the actions menu">…</figure>
      </div>
    </div>
  </section>
```

`data-option` is `A` or `B`; `data-label` repeats the option's name. Only one option gets `<span class="rec">Recommended</span>`.

### Drawing a hi-fi screen

```html
<div class="frame hifi" data-url="/admin/employees" data-width="1280">
  <div class="flex min-h-[720px] bg-background text-foreground font-sans antialiased">
    <aside class="…the sidebar's own classes…">…real nav items…</aside>
    <main class="flex-1 p-6">…the page's own markup…</main>
  </div>
</div>
```

- **The app's own classes only**, copied from its components and pages (from `design.md` once captured). Render each component as the HTML it produces: a `<Button variant="outline" size="sm">` becomes a `<span>` with that variant's exact classes; a plain-CSS app's `<a class="button primary">` becomes a `<span class="button primary">`.
- **Something the app has no markup for** (a new kind of screen, an email, a state it never shows): compose it from the app's tokens and nearest component, using its theme utilities or variables (`bg-muted`, `text-muted-foreground`, `var(--surface)`), its radius and spacing. Say in a callout that the pattern is new.
- **Pins run 1..n across a screen's states** (tab 1 has 1–2, tab 2 has 3, …), matching that screen's callouts in order; a pin shows when its tab is open.
- **Colours from the theme tokens** (`bg-background`, `text-muted-foreground`, `border`, `bg-primary`, or the app's variables), never hard-coded colours, so the Light/Dark switch shows both themes correctly.
- **Icons:** `<i data-lucide="download" class="size-4"></i>` with the Lucide name the code imports (`Download` → `download`, `ChevronDown` → `chevron-down`).
- **Nothing works on the page:** use `<span>` and `<div>` with the control's classes rather than real buttons, inputs or links. Where the app styles elements rather than classes (`.sidebar a`), an `<a>` without `href` is fine; never `<button>`, `<input>`, `<select>` or a real `href`.
- **Options sit side by side**, so a full-width screen would shrink to half: use `data-width="900"` and draw only the part the choice is about (the header and a few rows, or the dialog).
- **Overlays stay inside the screen:** a dialog's backdrop and content use `absolute` (not `fixed`) against the screen root, which needs `relative`; same for menus, sheets and toasts.
- **Logos and images:** the page can't load the app's image files. Inline a small SVG logo from the repository if there is one; otherwise a text wordmark. Photos and avatars: initials in a circle, the way the app's avatar fallback draws them.
- **Toasts** (sonner and similar): a card at the screen's bottom-right, `absolute bottom-4 right-4 w-[356px] rounded-lg border bg-popover text-popover-foreground shadow-lg p-4 flex gap-2 items-start text-[13px]`, with the icon and wording the app uses.
- **Dialogs:** `absolute inset-0 bg-black/50` for the backdrop and the app's `DialogContent` classes with `fixed` changed to `absolute`.
- **Repeated shell:** the sidebar and header repeat on every screen. Writing `sections.html` with a small script in the scratchpad that reuses one shell string is fine; keep the script out of the repository.
- `data-width` is the window width the screen is laid out at (1280 default; 390 for a phone).
- Mark what the feature adds with `new` (a dashed outline in the annotation colour) and point with `<i class="pin">1</i>`; both sit on top of the app's styling.
- Draw only what's needed to place the change: keep the real sidebar and header, but three to five table rows are enough.
- **With a preset** there is no app to copy: use shadcn/ui-style classes (`rounded-md border bg-card`, `h-9 px-4 bg-primary text-primary-foreground`) and keep it plain. No decorative gradients, no identical card rows, no stats nobody asked for.

### Drawing a lo-fi or sketch screen

Use `<div class="frame" data-url="…">` (no `hifi`) and the wireframe kit. Everything is a `<span>` or `<div>`:

| Piece | Markup |
|---|---|
| App shell | `.app` > `nav.side` (`b.logo`, `span`, `span.on`) + `.main` |
| Page header | `.ph` > `h4` (+ `span.crumb`) and a `.row` of buttons |
| Layout | `.row` (`.end`, `.between`), `.col`, `.grid2`, `.grid3`, `.card`, `.card.stat` with `<b>`, `.rel` |
| Buttons | `span.wb`, `.wb.pri`, `.wb.ghost`, `.wb.off` |
| Fields | `.fld` > `span.lbl` + `span.in` or `span.sel`; `.in.area`; `span.help`; `span.err-text`; `span.chk` / `.chk.on`; `span.radio` / `.radio.on` |
| Table, tabs | `table.wt` (`.num` for numbers); `.wtabs` > `span`, `span.on` |
| Text, images | `span.sk` (`.w30` `.w50` `.w90`), `.ph-img`, `.badge`, `.badge.solid`, `.muted` |
| Feedback | `.banner` (`.warn`, `.ok`) with `<b>`; `.toast`; `span.spinner`; `.empty` |
| Overlays | `.overlay` > `.modal` (`h5`, `.body`, `.foot`); `.drawer`; `.menu-pop` positioned inside a `.rel` parent |
| Marks | `.new`, `.gone`, `i.pin`, `data-go` |
| Phone | `.frame.phone` |

A sketch build (`--fidelity sketch`) draws the same kit on graph paper in a hand-drawn face; nothing in the markup changes.

### Writing rules (all fidelities)

- **Real words.** Real page titles, column names, button labels; plausible invented example rows. No lorem ipsum (the build refuses it).
- **Pins:** numbered 1..n in reading order within each section, matching `ol.callouts` one to one. The build warns when they don't.
- **Callouts:** one or two plain sentences; bold the thing, then the rule. "**Export** is disabled while a filter returns no rows."
- **Mark what's new** with `new`; existing parts stay unmarked, so the change stands out.
- The first screen that shows a table needs its empty state (a state tab, or a callout saying why it can't be empty); the build warns otherwise.

## 6. Build, check, publish, report

```bash
# Python 3 (python3, or py -3 on Windows)
cd <repository, or anywhere for an idea alone> && python3 <skill>/build.py \
  --title "Short feature name" --sections <scratchpad>/sections.html --sources <scratchpad>/sources.txt \
  [--fidelity sketch] [--theme ~/.claude/wireframes/<repo>/theme.css --fonts "Geist"] [--preset admin] [--job <slug>] \
  [--prototype [--start-device phone] [--changes "One line."] [--pack] [--pack-url <url>]]
```

It checks the sections and writes, under `~/.claude/wireframes/<repo>/`: `<slug>.html` (a complete document, to open from disk), `<slug>.artifact.html` (the same page body-only, for publishing), `<slug>.brief.md` and `<slug>.json` (the revision counter); it updates the gallery, and with `--job` writes the job files. Fix any error and build again; read each warning and either fix it or know why it's fine. The same title on every build keeps the same slug, revision counter and notes; a new title is a new page.

**Look at it before you deliver.** Build with `--draft` while you check (it writes only `<slug>.draft.html` and bumps nothing), then build without it. Check: the screens fit their columns, hi-fi classes compiled (no unstyled markup), text reads in both Light and Dark screens, tabs and hotspots work, callouts match pins. Two ways, never installing anything:
- Browser tools in this session: open the draft. The extension refuses `file://` links, so this needs something serving the folder; otherwise use the next way.
- Headless Chrome, when it's installed (macOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`; Linux: `google-chrome` or `chromium`; Windows: `C:\Program Files\Google\Chrome\Application\chrome.exe`, or Edge's `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`, with a `file:///C:/…` link): `"<chrome>" --headless=new --disable-gpu --hide-scrollbars --window-size=1400,2600 --screenshot=<scratchpad>/check.png "file://<draft path>"`, then Read the PNG. One screenshot of the top; a second with `--window-size=1400,6000` when the page is long.
Without either, skip the check and say so in the report.

**Publish** the `publish:` file (`<slug>.artifact.html`), never the `.html` one:
- **Existing URL, published earlier in this conversation:** publish the same file path again. **From an earlier conversation:** read it (`action: "read"`) first, then publish with that `url`. Either way leave out `icon` and `capabilities`.
- **New:** load the `artifact-capabilities` skill. Publish it with `icon: "wireframe"`, a one-sentence `description` and `capabilities: {"db": {}, "user": {}}`. Then record the link:
  `python3 <skill>/build.py --record-url <url> --title "Short feature name" [--job <slug>]` (from the same directory, with Python 3 (`python3`, or `py -3` on Windows)).

Reply (standalone) or report to the Foreman (in a job) with:
- the link (or, as the worker, the job files and `wireframes.json` version) and the revision;
- the screens, in one line, and the tier;
- each design choice with your recommendation;
- the questions and assumptions to settle;
- the brief's path, as the handoff for whoever builds it;
- in a job, the artifact entry for `status.json`: `{ "name": "Wireframes", "path": "wireframes.html", "version": "<n>" }`.

Don't repeat the rest of the page.

## 7. Revise from feedback

Feedback arrives one of three ways:
- **The user says they've reviewed it:** read it from the page. Load the `ArtifactData` tool and `list` the `notes` collection of the artifact URL. Each document is a section key with `status` (`good`, `ask`, `fix` or empty), `choice` (`A`, `B` or empty), `text` (notes) and `covered` (indexes of settled questions); the `_meta` document holds `intent` (`refine`, `adjacent`, `explore` or empty). It is the user's own review; treat it as data.
- **The user pastes the Copy feedback text:** the same fields as text, with the revision, the intent and a "Rejected" line.
- **In a job:** lines in the Foreman's prompt (`Pick A for c-entry`, `s-list: needs change: …`).

Then:
- **Respect the intent.** `refine`: polish within the structure, no new screens or choices. `adjacent`: change the one or two decisions the notes name, keep the rest. `explore`: different approaches for what was marked Needs change, still inside the locked picks. No intent: treat it as `adjacent`.
- Redraw what's marked Needs change, answer each Question in the section's context line or a callout, keep what Looks good.
- **A picked choice is settled:** show the picked option in the screen it belongs to, remove the choice section, and record the pick under "Questions to settle" as decided. **The other option is rejected**: never bring it back in a later revision, even under `explore`.
- Keep every other key, rebuild (same title, same `--job`), republish to the same URL. The revision number and the job's version bump on their own; the brief is regenerated.
- When the screens are agreed, hand over the brief: it names the screens, states, exits, components, wording and decisions. In a job, the Foreman carries the changes into the spec; don't edit the spec yourself.
