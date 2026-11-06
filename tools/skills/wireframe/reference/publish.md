# publish.py

Puts a prototype on the prototypes site and brings its notes back as the Foreman's feedback lines. Python 3, no dependencies. The site's API is built to this page: if the two disagree, change them together.

```bash
python3 <skill>/publish.py --job <slug>                     # a /feature job (Starbase's Publish button runs this)
python3 <skill>/publish.py --page <slug>.html --title "…"   # a page outside any job
python3 <skill>/publish.py --notes --job <slug>             # new notes (Starbase's Pull notes runs this with --json)
python3 <skill>/publish.py --notes --key <key>              # the same, by key
python3 <skill>/publish.py --import-notes <file> --key <key>  # the pilot: copy an artifact's notes, once
```

## Flags

| Flag | Goes with | What it does |
|---|---|---|
| `--job <slug>` | publish, notes, import | Works on the job folder (`$STARBASE_FEATURES_DIR`, else `$WORKSHOP_FEATURES_DIR`, else `~/.claude/feature-work`, then `<slug>/`). |
| `--page <html>` | publish, notes, import | Works on a built page outside a job. Give the `<slug>.html`, not `.artifact.html` or `.draft.html`. |
| `--notes` | `--job`, `--page` or `--key` | Prints new notes and picks as feedback lines. |
| `--since <iso>` | `--notes` | Starts from this time instead of the last pull. |
| `--import-notes <json>` | `--key`, `--job` or `--page` | Copies an artifact's export to the site. |
| `--title <text>` | publish | The feature's title. Default: `status.json`'s title in a job, the `.json`'s beside a page. |
| `--key <key>` | all | The feature's key. Used on the first publish; after that the record's key stands, and a different one is refused. |
| `--ticket <key>` | publish | Ticket key, such as `ORBIT-296`. A job's comes from `status.json`, else from a slug that starts `orbit-<n>`. |
| `--ticket-url <url>` | publish | Link to the ticket. A job's comes from `status.json`. |
| `--requirements <md>` | publish | Sends this file whole. A job otherwise sends the FR rows cut from its spec. |
| `--decisions <md>` | publish | Sends this file. A job otherwise sends its `decisions.md`. |
| `--pdf <file>` | publish | Sends this PDF. Otherwise the newest `*.pack.pdf` in the job folder, or `<slug>.pack.pdf` beside the page. |
| `--changes "<line>"` | publish | What changed. Default: this revision's note in the page's history. |
| `--site <url>` | all | Uses this site instead of the token file's. |
| `--dry-run` | all | Says what would be sent, with sizes, and sends nothing. Needs no token. Writes nothing. |
| `--json` | all | Publish and import print the site's reply. Notes print the reply plus `lines` (the feedback lines, unwrapped) and `since` (the time asked from). |

## The token file

`~/.claude/prototypes.json`, mode 600:

```json
{ "site": "https://prototypes.moxieorbit.com", "token": "ptp_…" }
```

Make the token on the site's Settings page and copy it here once. `site` is optional. The script refuses the file if anyone but its owner can read it, never prints the token, sends it only over https (or plain http to this laptop), and doesn't follow redirects, which would carry it elsewhere.

## Exit codes

Every failure is one line on stderr. Warnings start `warning:` and don't stop anything.

| Code | Means |
|---|---|
| 0 | Done. "No new notes" is a 0, with an empty stdout. |
| 1 | A problem here: a file, a value, a size. |
| 2 | Wrong flags. |
| 3 | The token file: missing, readable by others, broken, or no token in it. |
| 4 | The site refused, couldn't be reached, or gave an answer this script can't use. |

## What it remembers

After a publish it writes a record, and after a pull it adds `last_pull`:

```json
{ "key": "orbit-296-freeze-header", "site": "https://…", "url": "https://…/f/orbit-296-freeze-header",
  "revision": 4, "published_at": "2026-11-05T21:30:00+00:00", "last_pull": "2026-11-05T22:10:04.120Z" }
```

A job's record is `<job folder>/prototype.json`. A page's is `<slug>.prototype.json` beside it, because every page in a repository shares one folder. `--notes --key` finds the record holding that key. `last_pull` is the newest time in what the site sent, so a laptop clock that's wrong doesn't matter, and it never moves back. A pull from a site other than the record's touches nothing.

## The key

Ticket number plus the title's first four words when there's a ticket, the title's slug when there isn't. A ticket number already in the title isn't repeated: `ORBIT-465: Freeze/finalize team talent ratings` gives `orbit-465-freeze-finalize-team-talent`. Keys match `^[a-z0-9][a-z0-9-]{0,79}$`. Written once into the record, and never changed when the title or branch does.

## What it sends

### `POST /api/publish`

`Authorization: Bearer <token>`, `multipart/form-data`.

| Part | Kind | Always | Holds |
|---|---|---|---|
| `key` | text | yes | The feature's key. |
| `title` | text | yes | The feature's title. |
| `page_version` | text | yes | The page's own revision number, which isn't the site's revision. |
| `manifest` | text, JSON | yes | See below. |
| `page` | file `page.html`, `text/html; charset=utf-8` | yes | The complete page. |
| `ticket_key`, `ticket_url`, `job_slug`, `changes` | text | no | Left out when empty. |
| `requirements`, `decisions` | text, markdown | no | Left out when empty. |
| `pdf` | file `pack.pdf`, `application/pdf` | no | The stakeholder PDF. |

Reply, 200: `{ "key", "revision": 4, "url": "https://prototypes.moxieorbit.com/f/<key>", "created": false }`. `revision` must be an integer and `url` present, or nothing is recorded.

The manifest, the same shape from a job or a page:

```json
{ "version": 4, "title": "…", "tier": "hi", "fidelity": "high", "built_at": "<iso>",
  "screens":   [ { "key": "s-team", "name": "Team", "states": ["Phone"], "exits": [ { "label": "needs", "to": "s-needs" } ], "end": false } ],
  "choices":   [ { "key": "c-nav", "question": "…", "options": [ { "id": "A", "label": "…", "recommended": true } ] } ],
  "questions": [ { "kind": "decide", "text": "…" } ],
  "history":   [ { "rev": 4, "note": "…", "changed": [ { "id", "device", "name", "path" } ], "added": [], "removed": [] } ] }
```

`screens`, `choices`, `questions` and `history` are always lists. `title`, `tier`, `fidelity` and `built_at` may be missing. Paths on the laptop are never sent. `history[].rev` counts the page's revisions, not the site's.

### Sizes

A file's limit is in the table; 1 MB is 1,000,000 bytes.

| Part | Limit |
|---|---|
| `page` | 5 MB |
| `pdf` | 25 MB |
| `requirements`, `decisions` | 1 MB each |
| The whole request | 4.5 MB on Vercel |

Vercel takes 4.5 MB in one request and answers anything bigger with a 413, so the whole-request limit is what binds. The script refuses a bigger publish before sending, except to a server on this laptop.

### `GET /api/features/<key>/notes?since=<iso>`

`Authorization: Bearer <token>`. `since` is optional.

```json
{ "feature": { "key", "title", "ticket_key", "ticket_url", "latest_revision": 3 },
  "notes":   [ { "id", "revision": 3, "screen": "s-needs", "device": "phone", "kind": "change",
                 "text": "…", "pin": { … } | null, "by": { "name", "email" }, "at": "<iso>",
                 "updated_at": "<iso>", "deleted": false } ],
  "choices": [ { "group": "c-nav", "choice": "A", "by": { "name", "email" }, "at": "<iso>" } ] }
```

- With `since`, send what changed strictly after it, deleted notes included, compared at the precision the reply's times are written in. Postgres keeps microseconds and an ISO time from JavaScript keeps milliseconds, so compare truncated times or the last note comes back on every pull. The script also drops anything not newer than `since`.
- A note written by import has `"by": { "name": "<by_label>", "email": null }`.
- `choice` may be `""` when someone un-picks. It gets no line.

### `POST /api/features/<key>/notes`

`Authorization: Bearer <token>`, `application/json`. Import only, and the only way to set `by_label`: the site refuses `by_label` from a browser session. One request, all or nothing.

```json
{ "notes":   [ { "screen": "s-team", "device": "laptop", "kind": "question", "text": "…",
                 "pin": { "label": "Collection", "px": { "x": 442, "y": 272, "s": 1 } } | null,
                 "at": "<iso>", "by_label": "A person's name" } ],
  "choices": [ { "group": "c-nav", "choice": "A", "at": "<iso>" | null, "by_label": "…" } ] }
```

Reply, 200: `{ "notes": 12, "choices": 1 }`, the counts stored. A count that differs from what was sent is reported as a failure.

- The site keeps `at` as sent, so a second import can see what's already there; the script reads the notes first and leaves those out (same time and text; same group and choice).
- Notes attach to the feature's latest revision, since the artifact's revision numbers mean nothing on the site.
- These people have no site account, so `person_id` is empty on these rows and `by_label` holds the name, on notes and on choices.
- **`pin.px` is an artifact pin.** It's in pixels, with `s: 1` when it sits in the scrolling part, and has no `x`/`y` fractions, because a pixel can't become a fraction without the screen's size. Treat it as a pin with no fraction: the label still says where it was.

## Feedback lines

`--notes` prints the same lines the page's Copy feedback writes, inside the block Starbase's Screens tab uses:

```
--- Screens feedback (v3) ---
Pick A for c-nav
s-needs (phone, at "Theo Brandt"): needs change: Row is too tight
s-team (laptop, on r2): question: Who sees this?
--- end ---
```

- `v3` is the feature's latest revision on the site.
- Picks come first, then notes, each oldest first.
- `on r2` appears when the note was left on an older revision than the latest.
- A note's newlines become spaces, so one note is always one line and can't end the block early.
- Deleted notes and un-picked choices get no line.
- If people picked differently on one group, every pick is listed and a warning goes to stderr. Who said what is in `--json` (`by`), not in the lines.

Starbase wraps text in the block itself, so it uses `--json` and takes `lines`.

## The import file

`--import-notes` reads one JSON file holding what the artifact's data tool lists, plus names:

```json
{ "feedback": [ { "id": "…", "data": { "at", "author", "device", "kind", "name", "options", "path",
                                       "pin": { "label", "s", "x", "y" } | null, "rev", "role", "screen", "text" },
                  "version": 1, "updatedAt": "<iso>" } ],
  "notes":    [ { "id": "c-nav", "data": { "section": "c-nav", "choice": "A", "updatedAt": "<iso>" } } ],
  "names":    { "u_…": "A person's name" } }
```

- `feedback` is the artifact's `feedback` collection: one document per note, as `prototype.html` writes it. A list of the `data` objects works too. Page through with `next_cursor`, or the file is short.
- `notes` is the `notes` collection: one document per section. Only documents with a `choice` count, and `_meta` is left out. The page never recorded who picked, so a pick is labelled "Someone on the artifact".
- `names` maps `author` ids to names, from the data tool's `profiles` action. A note whose author isn't in it is labelled "Someone on the artifact", with a warning.
- A note with no text, an unknown kind or no time is left out and named in a warning.
- The data tool won't save other people's documents to a file with `out_dir`, so ask the person running the export before writing what it returns to a file yourself.
