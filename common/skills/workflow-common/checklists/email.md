# Email and notifications

- Send exactly when the spec says, to exactly whom it says, and at most once per triggering event (repeated clicks, retries and re-renders must not re-send).
- Sending failure follows the spec's failure behavior; it never silently drops or loops.
- Tests never send real email; they assert on what would be sent.

**Orbit** (source of truth: `src/lib/email/client.ts`)
- Send through `src/lib/email/client.ts`. `EMAIL_DEV_OVERRIDE` redirects all mail in dev and test.
- Never set `bypassDevOverride` on side-effect emails. It is reserved for explicit, admin-confirmed actions (invite, sign-in link).
- Templates live in `src/lib/email/templates/`. `npm run email` starts a preview server: it needs a separate yes.
- Internal-only content never appears in reporter-facing emails.
