---
repo: acme-billing
captured: 2026-10-21
stack: Next.js, plain CSS variables (app/src/app/globals.css)
sources:
  - app/src/app/globals.css
  - app/src/components/sidebar.tsx
  - app/src/components/actions-menu.tsx
  - app/src/components/confirm-dialog.tsx
  - app/src/components/toast.tsx
  - app/src/app/invoices/page.tsx
  - app/src/lib/roles.ts
---
# Acme Billing design

Example of the cache file the `wireframe` skill writes to `~/.claude/wireframes/<repo>/design.md` (hashes are added there by `build.py --design-stamp`). Acme Billing is a made-up app; nothing here is real.

## Theme
One stylesheet, `app/src/app/globals.css`: `:root` variables with a `.dark` override and plain class rules. `theme.css` keeps both variable blocks, moves the body font/background/colour to `.canvas`, prefixes every other selector with `.canvas`, turns the fixed backdrop and toast into absolute ones, and gives `.layout` a 640px minimum height instead of `100vh`. Inputs and selects are drawn as `<span class="field">` / `field select` with the input rule.

## Fonts
`--font: "Source Sans 3"` from Google Fonts. Pass `--fonts "Source Sans 3"`.

## Shell
`<div class="layout">` with `<nav class="sidebar">` (wordmark `<b>Acme Billing</b>`, then Dashboard, Invoices, Customers, Reports, Settings as `<a>`; the current one has `aria-current="true"`) and `<main>`. Every role sees the same five items.

## Components
- Page header: `.page-header` with `<h1>` and `.actions` on the right (`app/src/app/invoices/page.tsx`).
- Button: `.button`; primary `.button.primary`; disabled `aria-disabled="true"`. The dialog's confirm button renders as `<button class="primary">`: draw it as `<span class="button primary">` (theme.css styles `.dialog .primary` the same way).
- Actions menu: `.menu` with a `.summary` ("Actions ▾") and, when open, `.menu-list` of items (`actions-menu.tsx`). Secondary, less frequent actions.
- Filters: `.filters` row of status pills (`a`), a search input, a date-range select. `page.tsx` doesn't mark the current pill; the screens use `aria-current="true"` the way the sidebar does, and say so under Questions to settle.
- Table: plain `table`/`th`/`td`; `.amount` right-aligns; `.status` pill with `.overdue` / `.paid`.
- Empty state: `.empty`, "No invoices match these filters."
- Confirm dialog: `.backdrop` > `.dialog` with `<h2>`, one `<p>`, `<footer>` holding Cancel and a primary action (`confirm-dialog.tsx`). Every confirmation in the app uses it.
- Toast: `.toast`, bottom-right, one sentence ("Reminders sent to 4 customers").
- Notice: `.notice` banner, `.notice.error` for failures.

## Patterns and wording
Sentence case everywhere. Buttons name the action ("New invoice", "Send reminders", "Mark as paid"). Dialog titles are questions with a count ("Send 4 reminders?"). The empty state is one sentence, no illustration.

## Roles
`admin`, `billing`, `viewer` (`lib/roles.ts`). Only admin and billing see the page header's actions and New invoice; viewers see the list only.
