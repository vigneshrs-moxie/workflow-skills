# API routes, server actions and data access

- Every entry point checks authentication **and** authorization on the server. A hidden button is not a permission check. A direct request from a user without access must fail.
- Return only the fields the caller is allowed to see. Check what other users' data could leak through lists, search, counts or error messages.
- Validate input at the boundary. Failures return the states the spec describes, not raw errors.
- Writes that must happen together go in one transaction.

**Orbit** (source of truth: `AGENTS.md`, `../docs/plans/multi-office-engineering-brief.md`)
- API auth: `authenticateApiRequest` in `src/lib/api-auth.ts`. Role and feature checks: `src/lib/auth-permissions.ts`.
- Reads about people go through `getScope` / `scopeWhere` (`src/lib/scope.ts`). The `people` axis is a downline, `act` is entity-wide; swapping them breaks things silently.
- Internal-only data (internal notes, internal comments) never reaches reporter-facing pages, emails or search.
