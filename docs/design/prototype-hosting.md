# Hosting prototypes on an Orbit subdomain

A plan, not built yet. Prototypes are published as private Claude artifacts today; this moves them to a site stakeholders open with the same Google account they use for Orbit.

## The site

- **Address:** `prototypes.moxieorbit.com` (chosen 2026-11-04). One site for every feature: `/field-team-mobile` is the latest revision and `/field-team-mobile/r4` is a fixed one.
- **Repository:** `Moxie-Pest-Control-Phoenix/orbit-prototypes`, its own Vercel project. Nothing in Orbit's release process changes.
- **Pattern:** the same as hosted Starbase (`hosted/` in the Starbase repository): Google sign-in, Neon Postgres and one function.

A new feature needs no new setup. It is a new folder.

```
orbit-prototypes/
  site/                     sign-in, the feature list, the feedback API
  features/<slug>/
    feature.json            title, status, ticket, Starbase job, who can see it
    sections.html           the source, for the next revision
    r1/index.html           each published revision
    r1/pack.pdf             its stakeholder PDF
    r1/brief.md             the build brief
```

## Storage

| What | Where | Why |
|---|---|---|
| Pages, PDFs, briefs | The repository | History and review come free. About 2 MB per revision, so 30 features with 5 revisions each is about 300 MB. Move old revisions to private Blob storage if it grows past that |
| Notes, pins, choices | Neon Postgres, its own database | Written all day by many people, so they can't live in Git. A separate database keeps Orbit's production schema out of it |
| Who may see what | `feature.json` | Reviewed like code |

Notes carry `feature`, `revision`, `screen`, `device`, `role`, `pin`, `kind`, `text`, `author_email` and `created_at`, so they survive new revisions and stay attached to the exact screen.

## Login

A subdomain doesn't share Orbit's login by itself. Orbit's session cookie belongs to `www.moxieorbit.com`, so the new site needs a way to know who someone is.

**Decided 2026-11-04: the same Google sign-in, with the site's own session.** Stakeholders click Sign in with Google and, if they're already signed in, that's one click. The site gets their verified `@moxiepestcontrol.com` email, which is the same email as their Orbit profile, and stores notes under it. A small read-only Orbit endpoint can confirm the person is active and return their role. Orbit's login stays untouched.

**Not recommended yet: sharing Orbit's cookie across `*.moxieorbit.com`.** It gives true single sign-on, but it changes production login and sends Orbit's session token to every subdomain.

**People outside Moxie** have no Workspace account. Add an emailed one-time link per feature when that first comes up.

**Access:** by default anyone with an active Orbit profile can open a prototype. `feature.json` can narrow it to named emails or roles.

## How a feature gets there

1. The `/feature` Screens stage builds the prototype. Starbase shows it from the job folder, as it does now.
2. On your go-ahead, the Foreman copies the page, PDF and brief into `features/<slug>/r<n>/` on a branch and opens a PR. Merging publishes it in about a minute.
3. Stakeholders test and leave notes at `prototypes.moxieorbit.com/<slug>`.
4. Starbase pulls the notes and choices with a read token and shows them on the job's gate card, in the lines the Foreman already reads. The Foreman revises, and a new revision goes up with What's new filled in.
5. Raj's sign-off and the link go into `decisions.md`, then the build starts.

## What changes in the page

Only where notes are saved. The page keeps one small storage layer, which talks to the artifact database today and would talk to `/api/<slug>/feedback` on the site. Tailwind compiles in the browser today; the site could compile it at publish time so pages open faster.

## To set up

1. Create the repository and Vercel project.
2. Add the subdomain under the Vercel project's Domains. `moxieorbit.com` DNS is on Vercel with a wildcard, so no new DNS record should be needed. Follow `docs/hosting/vercel-setup.md` in the Starbase repo.
3. Add the site's address to a Google OAuth client restricted to the Workspace.
4. Create the Neon database.
5. Add the read-only Orbit endpoint, through the normal PR process.
