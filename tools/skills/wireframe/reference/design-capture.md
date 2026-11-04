# Capturing an app's design for hi-fi screens

Hi-fi screens use the app's own CSS, compiled in the page by Tailwind's browser build. You capture that CSS once per repository into a small cache, reuse it on later runs, and refresh it when the source files change.

## The cache

`~/.claude/wireframes/<repo>/` holds:

- `theme.css`: what `build.py --theme` loads. Tokens, variables and the component rules the screens need.
- `design.md`: what you learned about the app, so the next run doesn't re-read the repository. Its frontmatter lists the files it came from with their hashes.

Before reading any stylesheet, run `python3 <skill>/build.py --design-check` from the repository:

| It says | Do |
|---|---|
| `fresh` | Read `design.md` and `theme.css`. Still read the page the feature touches, and any component `design.md` doesn't cover. |
| `stale, changed since capture: …` | Re-read the changed files, update both cache files, run `--design-stamp`. |
| `none` | Capture (below), write both files, run `--design-stamp`. |

`design.md` shape:

```markdown
---
repo: acme-billing
captured: 2026-10-21
stack: Next.js, plain CSS variables
sources:
  - app/src/app/globals.css
  - app/src/components/sidebar.tsx
  - app/src/components/confirm-dialog.tsx
---
# Acme Billing design

## Theme
Where the tokens live, how theme.css was made from them, what was dropped.

## Fonts
`--font-geist-sans` → Google Fonts "Geist" (pass `--fonts "Geist"`).

## Shell
The sidebar and header: files, the classes of the shell, nav items per role, which item is active where.

## Components
One line each: name, file, the exact class string per variant you'll need.
- Button: `components/ui/button.tsx` · default `inline-flex items-center …` · outline `… border bg-background …` · sm `h-8 px-3`
- Dialog: …

## Patterns and wording
How the app does dialogs, menus, toasts, banners, empty states, tables and filters, with the words it uses ("No invoices match these filters.").

## Roles
Role names and what each sees in the shell.
```

Hashes are added by `--design-stamp`; leave them off when you write the file. List every file the capture depended on, so a change to any of them shows as stale.

## What goes in theme.css

Whatever the stack, the file must:

- define the colour, radius and font tokens the screens use;
- carry the `.dark` variant when the app has one, so **Screens: Light/Dark** works;
- scope every element rule to `.canvas` (`table` becomes `.canvas table`), or it restyles the review page;
- contain no `@import` (the build drops them and warns), no `html`/`body` rules, no `</style>`.

`build.py` loads Tailwind in the page whatever the stack, so utility classes (`flex`, `gap-2`, `p-4`) always work alongside the app's own classes. Tailwind's reset also applies inside the screens: headings lose their size and weight, lists their bullets, tables their borders. An app that relies on browser defaults for those needs them set in theme.css (`.canvas h1 { font-size: 22px; font-weight: 700 }`).

## Recipes by stack

Find the stack from `package.json` and the global stylesheet (`globals.css`, `app.css`, `index.css`, `styles/`).

### Tailwind v4, CSS-first (shadcn/ui and most new Next.js apps)

Signs: `@import "tailwindcss"` and `@theme` in the global stylesheet; `components/ui/*` with `cva(...)`.

- Keep `@custom-variant`, `@theme` / `@theme inline`, the `:root` variables and the `.dark` variables, unchanged.
- Drop every `@import` and page-specific rules.
- Keep the `@layer base` rule that sets border and outline colours, scoped: `*` becomes `.canvas *`. Drop the other base rules (`html, body`, cursors) and every rule outside a layer (scrollbars, `main`, page tweaks).
- `@import`s such as `tw-animate-css` or `shadcn/tailwind.css` add animations and state variants (`data-[state=open]:…`). A still screen doesn't need them: write the classes of the state you're showing.
- Components: read `button`, `badge`, `table`, `dialog`, `dropdown-menu`, `input`, `select`, `card`, `tabs`, `sheet`, the toast, and copy their **class strings exactly**, including the variant you need from each `cva(...)`. Put them in `design.md` under Components.

### Tailwind v3 (`tailwind.config.js|ts`, `@tailwind base;`)

Signs: `tailwind.config.*` with `theme.extend`; `@tailwind base; @tailwind components; @tailwind utilities;` in the stylesheet.

The page compiles with Tailwind v4, so translate the config into a `@theme` block:

| In the config | In theme.css |
|---|---|
| `theme.extend.colors.brand.500: "#2563eb"` | `@theme { --color-brand-500: #2563eb; }` |
| `colors.primary: "hsl(var(--primary))"` | `@theme inline { --color-primary: hsl(var(--primary)); }` and keep the `:root`/`.dark` variables |
| `fontFamily.sans: ["Inter", ...]` | `--font-sans: "Inter", ui-sans-serif, sans-serif;` |
| `borderRadius.lg: "var(--radius)"` | `--radius-lg: var(--radius);` |
| `screens.xl: "1280px"` | `--breakpoint-xl: 1280px;` |
| `darkMode: "class"` | `@custom-variant dark (&:is(.dark *));` |

Class names mostly carry over. Rename the ones that changed in v4 when you copy a component: `shadow-sm`→`shadow-xs`, `shadow`→`shadow-sm`, `rounded-sm`→`rounded-xs`, `rounded`→`rounded-sm`, `outline-none`→`outline-hidden`, `ring`→`ring-3`, `bg-opacity-50`→`bg-black/50` form, `flex-shrink-0`→`shrink-0`, `flex-grow`→`grow`.

### Plain CSS, SCSS or CSS modules

Signs: a stylesheet with `:root { --… }` and class rules; components use `className="button primary"` or a `styles.button` module.

- Copy the `:root` variables (and `.dark` or `[data-theme="dark"]` ones; rename a `[data-theme="dark"]` selector to `.dark` so the theme toggle works).
- The `body` rule's font, background and colour move to `.canvas { … }`; the rest of it is dropped.
- Copy the rules for the classes the screens use (shell, header, buttons, inputs, table, badges, dialog, toast, empty state), each selector prefixed with `.canvas `: `.button.primary` → `.canvas .button.primary`, `table th` → `.canvas table th`. Resolve SCSS nesting and variables by hand.
- `position: fixed` (backdrops, toasts) becomes `absolute`, and a `100vh` layout gets a fixed `min-height`, so overlays stay inside the screen.
- Rules on `input`, `select` and `button` elements: keep them under a class (`.canvas .filters .field`) and draw those controls as `<span class="field">`, since the screens hold no real controls. A component that renders `<button class="primary">` needs the same rule reachable from a span: write `.canvas .dialog .primary` next to `.canvas .button.primary`, and say in design.md how to draw it.
- Drop resets, `html`/`main` page layout, print styles, and anything the screens don't show.
- Draw with the app's class names, exactly as the components render them, so a reviewer who knows the app recognises the markup. `example/hifi/` in this skill shows the result for a small plain-CSS app.

### Theme objects in code (MUI, Chakra, Mantine, styled-components, Emotion)

Signs: `createTheme({ palette, typography, shape })`, `extendTheme`, a `theme.ts` exporting an object.

- Write a `@theme` from the object: `--color-primary`, `--color-secondary`, `--color-background`, `--color-foreground`, text colours, `--font-sans`, `--radius-*`, spacing unit.
- Draw the components with Tailwind utilities that match their rendered look (height, padding, radius, weight). Say in the overview that components are approximated from the theme, and add a `Decide` question if a component's look matters to the decision.

### No design system

An idea with no repository, a repository with no stylesheet, or a prototype where the brand isn't decided: build with `--preset admin|consumer|mono`.

- `admin`: cool and dense, for consoles and internal tools.
- `consumer`: warm and roomy, for customer-facing screens.
- `mono`: monochrome with one dark primary, when colour would distract.

The tier chip reads "Hi-fi · preset" and the meta line says the look is a placeholder. Add an `Assumed` line under Questions to settle: "No design system; the preset stands in for one." Don't write a design.md for a preset.

## Fonts

Fonts loaded through `next/font` (e.g. `--font-geist-sans`) aren't in the stylesheet. Add the variable to `:root` in theme.css with the Google Fonts family and a fallback, `--font-geist-sans: "Geist", ui-sans-serif, system-ui, sans-serif;`, and pass the families to `--fonts "Geist,Geist Mono"`. Record the mapping in design.md. A font that isn't on Google Fonts gets its fallback stack and a line in design.md saying so.

## Logos and images

The page can't load the app's image files. Inline a small SVG logo from the repository if there is one; otherwise a text wordmark in the logo's place. Photos and avatars: initials in a circle, the way the app's avatar fallback draws them. Note the choice in design.md so every run does the same.
