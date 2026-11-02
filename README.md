# Claude feature workflow

Skills and worker agents for [Claude Code](https://claude.com/claude-code) that take a feature or bug from a one-line request to reviewed pull requests, with a human sign-off at every stage.

You talk to one **Foreman** (the `/feature` skill). It hands each stage to a worker agent, checks the result against the files on disk, and gives you a short brief to approve before anything moves on. The [Feature Workshop](https://github.com/vigneshrs-moxie/feature-workshop) dashboard shows these jobs in a browser; it needs this workflow installed.

## Install

You need Claude Code installed and logged in (`claude` works in your terminal).

```sh
git clone https://github.com/vigneshrs-moxie/claude-feature-workflow.git
cd claude-feature-workflow
./install.sh
```

The script does three things:
- Links `skills/*` into `~/.claude/skills/` and `agents/*.md` into `~/.claude/agents/`. Because they are links, `git pull` here updates them in place.
- Moves anything already there with the same name to `~/.claude/backups/claude-feature-workflow/<date>/`, outside the skills folder so Claude Code doesn't load it twice.
- Clones the [git workflow docs](https://github.com/vigneshrs-moxie/moxie-portal-git-workflow) to `~/Projects/moxie-portal-git-workflow`, or updates them if already cloned. The Foreman reads them before any branch or PR step. Keep that location; the skills look for it there.

Run it again after every `git pull`. Set `CLAUDE_DIR` to install somewhere other than `~/.claude`.

Then in Claude Code, inside the repository you work on:

```
/feature Add a "Download CSV" button to the invoices page
```

## What is in here

### Skills (`skills/`)

| Skill | What it does |
|---|---|
| `feature` | The Foreman. Runs clarify → spec → screens → investigate → plan → build → test → review → PRs through the agents below, one brief per stage. Also holds the rules every worker follows, the job options (how much process a job gets), the git workflow summary, and the review checklists. |
| `feature-spec` | Drafts a product spec from a request and recommends the small or large route. Holds `workflow-gates.md`, the rules for what each stage needs before it may start. |
| `feature-refine` | The detailed product interview for a large feature, one question at a time. |
| `feature-investigate` | Read-only look at how the repository behaves today, written up as private findings. |
| `feature-plan` | The implementation plan and test plan, from the spec and findings. |
| `wireframe` | Draws the screens for a feature or product idea and publishes them as a private review page before anything is built. Four fidelities: text in the reply, hand-drawn sketch, greyscale lo-fi, and hi-fi in the app's own design (read from the repository and cached, or a bundled preset when there is no design system). One panel per screen in flow order, states as tabs, Before/Now for changed screens, numbered notes, clickable exits between screens, and two side-by-side options wherever there is a real design choice. Reviewers mark, pick and annotate on the page; it also writes a build brief and keeps a gallery of every page. Works in any repository or with none. `example/` holds a lo-fi and a hi-fi demo on a made-up billing app. |
| `feature-wireframe` | The Screens stage of a `/feature` job: runs `wireframe` in job mode (no questions, files to the job folder, nothing published) for the Foreman and the Feature Workshop. |
| `ship` | Moves a finished branch through the three PR stages from the terminal: fork branch → same-named org branch (PR #1, you self-review and merge), org branch → staging (PR #2, Raj reviews), staging → main (PR #3, the release summary), and the sync route when PR #2 conflicts with staging. `preflight.py` is read-only: remotes, PR state on GitHub, the only-my-commits check, a merge simulation, migration numbers against main and staging, risk flags, CI. PR bodies follow `pr-body.md`. It opens a PR only when you say so and never merges, approves or pushes to staging or main. |
| `review-walkthrough` | Builds a one-page cue sheet for an in-person review of a branch or PR. Changes are sorted into four zoom levels (System, Module, Function, Line); Quick shows only the highest level with changes, with Explain jumps to a short before/now explanation, and a view picker shows all levels or any one. A wrap-up collects follow-ups. |
| `uat-guide` | Writes a one-to-two page UAT guide for non-technical stakeholders testing a feature on staging: what it does, how to try it, and what is missing by design, plus an optional feedback deadline. It is written as a Claude Docs doc and exported as a Letter PDF (`save_pdf.py`) to send to testers. Technical notes for you stay in the chat reply. `example.md` is the approved Announcements guide. |

### Agents (`agents/`)

Each file sets a worker's model, effort and tools. The Foreman dispatches them; you never call them directly.

- **Writers:** `feature-spec-writer`, `feature-wireframer` (draws the spec's screens with the `wireframe` skill in job mode), `feature-investigator`, `feature-planner`, `feature-implementer`, `feature-tester`.
- **Review lenses**, run in parallel on the finished code: `feature-reviewer` (spec conformance), and `feature-review-permissions`, `-db`, `-tests`, `-ui`, `-errors`, `-performance`, `-conventions`.
- **`feature-fable-check`:** a short, independent second look at one document or change, on request.

## Screens before building

Run `/wireframe <idea>` (or pass a spec path) inside the repository the feature belongs to, or anywhere for an idea with no code yet. You get a link to a private page:

- **Four fidelities.** Say "in chat" for a text wireframe in the reply, "sketch" for a hand-drawn page, "low-fi" for greyscale boxes, or nothing: inside a repository with a design system the screens come **in the app's own design**. The theme and component classes are captured once into `~/.claude/wireframes/<repo>/design.md` and reused; Tailwind v4, Tailwind v3 and plain CSS apps all work, and three bundled presets (admin, consumer, mono) stand in when there is no design system. A tier chip on the page says what that fidelity decides and what it leaves open.
- **Screens: Light/Dark** shows both themes; **100%** shows a screen at actual size.
- **Pink dashed outlines** mark what the feature adds; numbered pins match the notes under each screen. Controls that open another screen are clickable, each screen lists where it goes, and the overview carries a map.
- **Design choices** show two options side by side, one marked Recommended. Pick one with **Pick A / Pick B** (or the `A` / `B` keys). A rejected option never comes back.
- **Verdicts and notes** per screen save with the page, along with how far the next round may go (refine, adjacent, explore). Tell Claude you've reviewed it and it reads them from the page, or use **Copy feedback** and paste. It revises the same page; a states coverage table in the wrap-up shows which empty, error and loading views were drawn.
- **Questions to settle** lists open decisions and the assumptions it made.
- **A build brief** (`<slug>.brief.md`) lists the screens, states, exits, components, wording and decisions, for whoever builds it. Every page is listed in the gallery at `~/.claude/wireframes/index.html`.

Inside a `/feature` job the `feature-wireframe` wrapper runs the same skill as the **Screens** stage: the `feature-wireframer` worker draws the screens from the agreed spec and writes `wireframes.html` (opens straight from disk; the Feature Workshop shows it in its Screens tab, where verdicts and notes save in the browser), `wireframes.json` (screens, exits, choices, questions, version) and `wireframes.brief.md` to the job's folder. Nothing is published; your picks and notes come back as lines in your reply to the gate card. It only reads the repository (no servers, builds or tests) and invents all example data.

## How a job runs

1. **Clarify.** For a standard or large job, the Foreman first asks up to five questions that would change what gets built, each with options, a recommendation and what each option means. Often there are none, and it goes straight to the spec.
2. **Spec.** The Foreman drafts a spec from your request and answers, and asks at most three questions.
3. **Route.** Each job gets a level of process, from a gate-free tweak to a full panel review. The Foreman suggests one from the request and the code it touches; you confirm or change it. Risky changes (migrations, auth, scoping, email) always get more review.
4. **Screens.** When the spec names a page, dialog, sheet or email, the screens are drawn for review before any code; what you pick goes into the spec. Skipped when there is nothing to draw.
5. **Investigate and plan.** Read-only findings, then a plan you approve before any code is written (a tweak at L0 builds straight from your request).
6. **Build.** A fresh implementer per plan step, one local commit per step, in its own git worktree.
7. **Test and review.** The test plan runs; review lenses report; fixes get one round by default.
8. **PRs.** Pushed to your fork only. Pull requests to the organisation repository are opened only when you say so.

Every job keeps its own private folder under `~/.claude/feature-work/<slug>/` with the spec, findings, plan, briefs and a `status.json` the dashboard reads. Nothing from that folder is committed to the repository you are working on.

## Adapting it

- `skills/feature/git-workflow.md` and `skills/feature-spec/workflow-gates.md` describe one team's remotes, branch naming and PR stages. Edit them for yours.
- `skills/feature/checklists/` holds the review checklists per area (API, database, email, UI). Add your own.
- Model choices live in each agent's front matter; a job's options can set the build and test models per job.

## Credits and license

Planned changes for test-first building, checking before claiming done, and systematic debugging draw on ideas from [Superpowers](https://github.com/obra/superpowers) by Jesse Vincent (MIT). They are rewritten in this workflow's own words.

MIT licensed. See [LICENSE](LICENSE).
