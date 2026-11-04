# Layer checklists

The conductor hands the implementer the checklist for each layer a plan step touches (the plan tags every step with its layers). Review lenses use the same files as their reference.

Each checklist points at the repository's own docs as the source of truth and adds only the traps those docs warn about. When a repo doc and a checklist disagree, the repo doc wins; report the drift so the checklist can be fixed.

Sections marked **Orbit** apply to moxie-portal-vrs (paths relative to `app/`).

- [all.md](all.md): every step
- [db.md](db.md): schema, migrations, queries that change shape
- [api.md](api.md): routes, server actions, server-side data access
- [ui.md](ui.md): pages, components, user-facing text
- [email.md](email.md): email and notifications
