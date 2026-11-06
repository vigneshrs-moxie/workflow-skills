# Database and migrations

- A schema change is the migration plus every place that reads or writes the changed shape.
- Write migrations that are safe to apply once, in order, against live data. Say what happens to existing rows.
- Applying a migration anywhere is never part of implementation: it needs a separate yes.

**Orbit** (source of truth: `prisma/migrations/README.md`; multi-office rules: `../docs/plans/multi-office-engineering-brief.md`)
- Migrations are raw SQL in `prisma/migrations/00NN_name/migration.sql`. The number is picked at **PR time** (highest on `moxie/main` + 1). Use the next number now, and flag in the log that it must be re-checked at PR time (`npm run db:renumber` exists).
- `schema.prisma` is maintained by hand: a schema change is the SQL plus the model edit, then `prisma generate`.
- Never run `prisma migrate dev`, `prisma db push` or `prisma migrate reset`: they treat the schema as drift and offer to reset it.
- Flag in the log, for a human:
  - a migration adding a column that already-shipping code reads (it must be applied **before** the code deploys; auto-apply runs after);
  - anything that could run longer than about 5 minutes.
- A new gated feature needs a seeding migration or it fails closed for every entity.
- New records are stamped from the **subject**, never the actor. Never hardcode an office or branch name; read `entity_branches`.
