---
name: uat-guide
description: Use when a feature is on staging and needs user acceptance testing by non-technical stakeholders (heads of operations, office admins, managers), and the user asks for a UAT guide, a testing write-up, a stakeholder brief, "what it is and how to try it", or a PDF to send testers before a production release.
---

# UAT guide

A one-to-two page guide that tells non-technical stakeholders what a feature does, how to try it, and what is missing on purpose. It is written as a Claude Docs doc and exported as a PDF to send to the testers. `example.md` is the approved Announcements guide: match its shape, length and tone.

## The shape

A UAT guide has exactly these parts, in this order:

1. **Title**: `<Feature> UAT Guide`.
2. **Byline**: the as-of date chip (today) · a mention of the user.
3. **Lead**: two sentences. The first says what the feature lets people do and what it replaces. The second is "Try it on [staging](<url>); if you like it, we release it to production."
4. **Deadline** (only when the user gives one): `**Deadline:** we want UAT finished <when>, so please send all feedback by <Weekday>, <date chip>.`
5. **`## What it does`**: 4–6 bullets, each `**Label**: one or two sentences.` Labels follow the feature's own flow, for example Write · Who sees it · How and when · What employees see · What admins see.
6. **`## Trying it`**: bullets for **Where** (the linked staging URL, then the plain URL in brackets so it survives print, the login or role, and the menu path, with screen names in bold: Admin → **Announcements**), **Safe to experiment**, and one bullet per way staging behaves differently from production. Where the user steps in, say it in their first person ("I'll forward you…", "tell me the time and I'll start them"). Write that only when the user has said they will do it. Where nobody needs to do anything, state the difference plainly ("Staging doesn't send reminders").
7. **`## By design (not bugs)`**: 3–6 bullets, `**Thing that is missing or locked.** One sentence on why, or what to do instead.`

Nothing else goes in the doc: no test scenarios, sign-off boxes, open questions, placeholders or sources.

## Steps

1. **Gather facts** from the feature's PR description, spec or plan, and check screen labels, menu paths and defaults in the code. Ask the user, in one message, only for what isn't written down: the staging URL; who tests, with which login, and which side they try (for example employee, manager or both); how each staging difference is handled (such as who forwards the redirected emails); and the deadline. A deadline date must be in the future and its weekday must match: check with `date`, and if it doesn't fit, use the date that does (for example, this Friday) and say so.
2. **Create the doc**, following the Artifact tool's flow: `quickstart` with intent `document`, then publish the Docs type it names, with `title` = the doc's title. That creates the empty doc. Land the skeleton in it with one connector `batch` (title, byline, lead, a pending block per section), then fill one section per `update`, as the Docs guide says.
3. **Export the PDF**: the connector's `export` with `format: "pdf"` and `paper: "letter"`, for the doc's tab. The result is usually too large to show, so it is saved to a file; decode it with `python3 -I <this skill>/save_pdf.py <saved result> "$HOME/Downloads/<Title>.pdf"`. Check page 1 with `qlmanage -t -s 1400 -o <scratch dir> <pdf>` and read the PNG.
4. **Reply in chat** with the doc link and the PDF path. Put anything technical the user needs, but the testers don't, in the chat reply rather than the doc. Examples: where staging emails really go, cron or quota limits, env settings to check. Remind the user that the doc is private until they share it.

## Writing rules

- Write for an operations reader: what they see and do, not how it works. No code names, tables, migrations, env vars, PR numbers or ticket ids.
- Use the screen's own words for buttons and menus, in bold.
- Sentences under 25 words, no emoji, no "this document…".
- Keep it to two Letter pages. If it runs longer, cut words, not sections.

## Common mistakes

| Mistake | Fix |
|---|---|
| Adding a test-scenario table or sign-off checklist | The user removed both. Testers explore on their own; feedback goes to the user. |
| "The team will…" / "contact support" | Use the user's first person: "I'll forward…", "tell me…". |
| A link only as text | Write `[Orbit staging](https://…) (staging.example.com)` so the PDF shows the address. |
| A deadline copied as typed when it's in the past | Check it with `date`; use the coming weekday and tell the user. |
| A placeholder like "link to add" left in the doc | Ask for the missing fact before writing. |
| Staging caveats explained technically in the doc | One plain bullet in the doc; the details go in the chat reply. |
