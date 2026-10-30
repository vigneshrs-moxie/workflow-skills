# Brief format and review checklist

## Review checklist (run before every brief)

Check the artifact **on disk**, not the worker's summary of it.

- **Traceable:** every V1 FR has an AC; every AC has a test in the test plan; every plan step cites FRs; every spec AC is covered by an item in `acceptance.md`, and every acceptance item by a line in `dev-tests.md`; dev tests are one line each, in plain words. For a quick plan or `requirements.md`: every numbered criterion has a check or a manual step.
- **Nothing invented:** no business rule, permission, audience, timing or notification behavior that the spec does not confirm. Recommendations stay labeled.
- **Evidence:** claims about the code cite file:line; spot-check two or three of the citations yourself.
- **Honest checks:** "ran" vs "proposed" is accurate; nothing claims a check passed that did not run.
- **In scope:** no scope creep beyond V1; nothing outside the allowed writes (application files only during implementation, on the feature branch).
- **Versions:** every artifact names the versions it is based on, and those match what is on disk.
- **Gates:** the worker stopped where it should and did not start the next stage.
- **Proportional:** a small enhancement did not get a large-feature treatment.
- **Key points:** the summaries (`status-json.md` §3) for every document this stage produced or changed, and for this brief, are written from the files on disk.
- **Options followed:** the level, stages, reviewers, checks and models match the job's `options.json` at the time.

## Brief format

Aim for about 12 lines; a brief asking to approve what will be built (a quick plan or a plan; at L0 usually none; the first brief shows the diff) may run to about 25, so the human can decide without opening a file. Plain language. No restating the artifact. Write the brief file and `status.json` with one Write each (never with scripts or several edits).

```
**<Feature> · <stage> done** · spec v<x> (<status>) · <other artifact> v<n>

**What happened**
- <3–5 bullets: the outcome, the biggest finding or change, anything surprising>

**Concerns** (from my review; omit if none)
- <issue> — <what I did about it or what it means>

**Decisions for you** (omit if none; max 3, recommendation first)
1. <question> — Recommended: <answer>. <one-line tradeoff>
2. …

**Next:** <proposed stage, one line on what it will and won't do>
Reply "go" to proceed<, or answer like "1a 2 yes">. Full details: <artifact paths>
```

When the human asks for detail on one point, answer that point from the artifact; do not paste the artifact.

### The clarify brief

Your own questions before the spec (SKILL.md, Start). No artifact, so no version in the headline and no "What happened". Up to five decisions, each with two or three options, the recommendation first, and one line per option on what changes if it is picked (the `consequence` in status.json). The level proposal, when there is one, is Decision 1.

```
**<Feature> · before the spec**

**Decisions for you** (max 5, recommendation first)
1. Who gets this? — Recommended: a.
   a. Phoenix only: one office rule, ships this week
   b. All offices: needs the scoping lens, L3
2. …

**Next:** the spec, with your answers as confirmed items
Reply with answers like "1a 2b", or "use your recommendations".
```

### The wireframe brief

The headline names the spec version drawn from and the wireframes version. "What happened" is the screens, one line each. Each design choice is a decision with A and B as the options and the worker's recommendation; the page's questions follow (max 3 decisions in all; the rest stay in "Concerns" as open items the page lists). "Next" says how to review and what the reply may carry.

```
**<Feature> · screens drawn** · spec v<x> · wireframes v<n>

**What happened**
- Employees list: the Export button sits with the page's other actions (admins only)
- Export dialog: format and filters, with the current filter set shown
- Done toast

**Decisions for you**
1. Where does the export start? — Recommended: A, button in the page header. B puts it in the actions menu, one click further.

**Next:** review the screens in Starbase (Screens tab) or open wireframes.html. Reply "go" to keep them as drawn, with picks like "Pick A for c-entry", lines like "s-dialog: needs change: show the row count", or paste the page's Copy feedback. Agreed screens go into the spec, then investigation.
```
