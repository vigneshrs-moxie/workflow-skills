#!/usr/bin/env python3
"""Publish a prototype to the prototypes site, and bring its notes back. See reference/publish.md.

Usage:
  python3 publish.py --job <slug>                  publish a /feature job's page, PDF, requirements, decisions
  python3 publish.py --page <slug>.html            publish a page outside any job
      [--title T] [--key K] [--ticket ORBIT-1] [--ticket-url U] [--requirements F] [--decisions F]
      [--pdf F] [--changes "One line."]
  python3 publish.py --notes (--job S | --page P | --key K) [--since <iso>]
                                                   print new notes as the Foreman's feedback lines
  python3 publish.py --import-notes <json> --key K  copy an artifact's notes to the site, once
Every mode takes --site <url>, --dry-run and --json.

The token is in ~/.claude/prototypes.json ({"site": "...", "token": "..."}, mode 600). It is never printed.
What was published is remembered in <job folder>/prototype.json, or <slug>.prototype.json beside a page.

Exit codes: 0 done; 1 a problem here (a file, a flag, a size); 2 wrong flags; 3 the token file;
4 the site refused, or couldn't be reached. Each failure is one line on stderr.
"""
import argparse, glob, http.client, json, os, re, sys, urllib.error, urllib.parse, urllib.request, uuid
from datetime import datetime, timezone

DEFAULT_SITE = "https://prototypes.moxieorbit.com"
LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1")
MB = 1000 * 1000
LIMITS = {"page": 5 * MB, "pdf": 25 * MB, "requirements": 1 * MB, "decisions": 1 * MB}
BODY_LIMIT = 4.5 * MB  # Vercel takes no more than this in one request, whatever the limits above say
TIMEOUT = 45  # seconds; under the 60 Starbase gives this script, so a slow site gets this script's message
KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
TICKET_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*-\d+$")
SHORT_TITLE_WORDS = 4
FR_ROW = re.compile(r"^\|[\s*~_]*FR-\d+")
TABLE_RULE = re.compile(r"^\|[\s:|-]+\|?\s*$")
WORDS = {"change": "needs change", "question": "question", "idea": "idea"}
# What the site may see of a build's summary. The rest (source, repo) are paths on this laptop.
MANIFEST_KEEP = ("title", "tier", "fidelity", "screens", "choices", "questions", "built_at")
UNNAMED = "Someone on the artifact"


class Stop(Exception):
    """A failure a person reads: one line and an exit code."""
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def warn(message):
    print(f"warning: {message}", file=sys.stderr)


def read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def read_file(path, label):
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError:
        raise Stop(1, f"Can't read the {label} at {path}.")


def read_text(path, label):
    try:
        return read_file(path, label).decode("utf-8")
    except UnicodeDecodeError:
        raise Stop(1, f"The {label} at {path} isn't UTF-8 text.")


def write_json(path, data):
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, indent=2) + "\n")
    os.replace(tmp, path)


def size(n):
    return f"{n / MB:.1f} MB" if n >= MB else f"{max(n, 1) / 1000:.0f} KB"


def one_line(s):
    return " ".join(str(s if s is not None else "").split())


def stamp(s):
    """An ISO time as an aware datetime, or None. (Python 3.9 can't read a Z or a short fraction.)"""
    m = re.match(r"^(\d{4}-\d\d-\d\d)[T ](\d\d:\d\d)(?::(\d\d))?(?:\.(\d+))?(Z|[+-]\d\d:?\d\d)?$", str(s or "").strip())
    if not m:
        return None
    day, minute, second, fraction, zone = m.groups()
    zone = "+00:00" if zone in (None, "Z") else f"{zone[:3]}:{zone[-2:]}"
    try:
        return datetime.fromisoformat(f"{day}T{minute}:{second or '00'}.{(fraction or '').ljust(6, '0')[:6]}{zone}")
    except ValueError:
        return None


# ---------- the token and the site ----------

def config_path():
    return os.path.join(os.path.expanduser("~"), ".claude", "prototypes.json")


def load_config():
    """(settings, problem). Nothing here prints the file's contents, and neither may a caller."""
    path = config_path()
    try:
        mode = os.stat(path).st_mode
    except OSError:
        return {}, f"Publishing isn't set up on this laptop: there's no {path}. See reference/publish.md."
    if os.name != "nt" and mode & 0o077:  # Windows has no such bits to read
        return {}, f"{path} can be read by other accounts, so it wasn't used. Run: chmod 600 {path}"
    cfg = read_json(path)
    if not isinstance(cfg, dict):
        return {}, f"{path} isn't valid JSON."
    if not isinstance(cfg.get("token"), str) or not cfg["token"]:
        return cfg, f"{path} has no token in it."
    return cfg, None


def pick_site(arg, cfg):
    site = (arg or cfg.get("site") or DEFAULT_SITE).rstrip("/")
    u = urllib.parse.urlsplit(site)
    if u.scheme == "https" and u.hostname or u.scheme == "http" and u.hostname in LOCAL_HOSTS:
        return site
    raise Stop(1, f"{site} won't do: the token only goes over https, or plain http to this laptop.")


def is_local(site):
    return urllib.parse.urlsplit(site).hostname in LOCAL_HOSTS


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """urllib would carry the Authorization header to wherever a redirect points."""
    def redirect_request(self, *args, **kwargs):
        return None


def refusal(e, missing):
    """The one line for an HTTP error."""
    if 300 <= e.code < 400:
        return f"The site answered with a redirect to {e.headers.get('Location', 'somewhere else')}, not an answer. Check the site address."
    said = ""
    try:
        said = one_line(json.loads(e.read().decode("utf-8")).get("error"))[:200]
    except (ValueError, AttributeError, OSError):
        pass
    plain = {401: "The site refused the publish token. Make a new one on the site's Settings page.",
             403: "The site says this token can't do that.",
             404: missing,
             413: "That's too big for the site to take in one request.",
             429: "Too many publishes this hour. Try again later."}.get(e.code, f"The site answered {e.code}.")
    return f"{plain} The site said: {said}" if said else plain


def call(site, token, method, path, body=None, ctype=None, missing="The site has no such feature."):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json", "User-Agent": "prototypes-publish"}
    if ctype:
        headers["Content-Type"] = ctype
    handlers = [NoRedirect()] + ([urllib.request.ProxyHandler({})] if is_local(site) else [])
    req = urllib.request.Request(site + path, data=body, method=method, headers=headers)
    try:
        with urllib.request.build_opener(*handlers).open(req, timeout=TIMEOUT) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        raise Stop(4, refusal(e, missing))
    except (urllib.error.URLError, http.client.HTTPException, OSError) as e:
        raise Stop(4, f"Couldn't reach {site}: {one_line(getattr(e, 'reason', e))}")
    try:
        reply = json.loads(raw.decode("utf-8"))
    except ValueError:
        reply = None
    if not isinstance(reply, dict):
        raise Stop(4, f"The site's answer wasn't the JSON this script expects. Check that {site} is the prototypes site.")
    return reply


def multipart(fields, files):
    """(body, content type). fields: {name: text}. files: {name: (filename, type, bytes)}."""
    boundary = "----prototypes" + uuid.uuid4().hex
    out = []
    for name, value in fields.items():
        out += [f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n'.encode("utf-8"),
                value.encode("utf-8"), b"\r\n"]
    for name, (filename, ctype, data) in files.items():
        out += [f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{filename}"\r\nContent-Type: {ctype}\r\n\r\n'.encode("utf-8"),
                data, b"\r\n"]
    out.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(out), f"multipart/form-data; boundary={boundary}"


# ---------- where things are ----------

def features_root():
    """The same folder build.py writes job files to."""
    return os.path.expanduser(os.environ.get("STARBASE_FEATURES_DIR") or os.environ.get("WORKSHOP_FEATURES_DIR") or os.path.join("~", ".claude", "feature-work"))


def job_folder(slug):
    if slug != os.path.basename(slug) or slug in (".", ".."):
        raise Stop(1, f"{slug} isn't a job slug.")
    folder = os.path.join(features_root(), slug)
    if not os.path.isdir(folder):
        raise Stop(1, f"No job folder at {folder}.")
    return folder


def page_stem(path):
    return path[:-5] if path.endswith(".html") else path


def state_file(a):
    """Pages share a folder, so a page's record carries its name; a job's folder is its own."""
    if a.job:
        return os.path.join(job_folder(a.job), "prototype.json")
    if a.page:
        return page_stem(os.path.expanduser(a.page)) + ".prototype.json"
    return None


def state_for_key(key):
    """The record that holds this key, when only --key was given."""
    pattern = [os.path.join(os.path.expanduser("~"), ".claude", "wireframes", "*", "*.prototype.json"), os.path.join(features_root(), "*", "prototype.json")]
    for path in (p for pat in pattern for p in glob.glob(pat)):
        state = read_json(path)
        if isinstance(state, dict) and state.get("key") == key:
            return path
    return None


def settled_key(a, state, made=None):
    """A key is written once and never changes (D18): the record's wins over everything."""
    key = state.get("key") or a.key or made
    if a.key and state.get("key") and a.key != state["key"]:
        raise Stop(1, f"This is already published as {state['key']}, and a key never changes. Drop --key.")
    if not key:
        raise Stop(1, "There's no key to work out from that title. Pass --key.")
    if not KEY_RE.match(key):
        raise Stop(1, f"{key} won't do as a key: lower-case letters, digits and dashes, 80 at most.")
    return key


def slugify(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def make_key(title, ticket):
    """D18: ticket number plus a short title when there is a ticket, else the title's slug."""
    if not ticket:
        return slugify(title)[:80].strip("-")
    short = re.sub(r"^\s*" + re.escape(ticket) + r"\b[\s:·–—-]*", "", title, flags=re.I)  # "ORBIT-465: Freeze…"
    return "-".join([ticket.lower()] + slugify(short).split("-")[:SHORT_TITLE_WORDS]).strip("-")[:80].strip("-")


def job_ticket(status, slug):
    """status.json's ticket.key, else a slug that starts orbit-<n>: Starbase's own rule (decisionPrefix)."""
    key = one_line((status.get("ticket") or {}).get("key"))
    if TICKET_RE.match(key):
        return key.upper()
    m = re.match(r"^orbit-(\d+)(?:-|$)", slug, re.I)
    return f"ORBIT-{int(m.group(1))}" if m else None


def fr_table(spec):
    """The spec's functional requirements: the FR rows under their own heading row, each id once."""
    lines, head, rows, seen = spec.splitlines(), [], [], set()
    for i, line in enumerate(lines):
        if not FR_ROW.match(line):
            continue
        fr = re.search(r"FR-\d+", line).group(0)
        if fr in seen:
            continue
        seen.add(fr)
        if not rows and i >= 2 and TABLE_RULE.match(lines[i - 1]) and lines[i - 2].startswith("|"):
            head = lines[i - 2:i]
        rows.append(line.rstrip())
    return "\n".join((head or ["| ID | Requirement | Source |", "|---|---|---|"]) + rows) + "\n" if rows else None


def find_spec(status, folder):
    named = (status.get("spec") or {}).get("path")
    if named:
        path = named if os.path.isabs(named) else os.path.join(folder, named)
        if os.path.isfile(path):
            return path
        warn(f"status.json names a spec that isn't there: {path}")
    others = sorted(glob.glob(os.path.join(folder, "*-product-spec.md")), key=os.path.getmtime)
    plain = os.path.join(folder, "spec.md")
    return plain if os.path.isfile(plain) else others[-1] if others else None


def newest(pattern):
    found = glob.glob(pattern)
    return max(found, key=os.path.getmtime) if found else None


def make_manifest(info, stem, version):
    """Screens, choices and the page's revision history: what the site shows around the page."""
    manifest = {k: info[k] for k in MANIFEST_KEEP if k in info}
    manifest["version"] = version
    history = read_json(f"{stem}.revisions/history.json") if stem else None
    manifest["history"] = history if isinstance(history, list) else []
    if "screens" not in manifest and stem:  # beside a page the build keeps only a revision counter
        try:
            sys.dont_write_bytecode = True  # no __pycache__ in the skill's folder
            from build import summary_prototype
            with open(f"{stem}.revisions/{version}.html", encoding="utf-8") as f:
                manifest.update(summary_prototype(f.read()))
        except (ImportError, OSError):
            pass
    for k in ("screens", "choices", "questions"):
        manifest.setdefault(k, [])
    return manifest


def checked_name(path):
    if path.endswith(".artifact.html"):
        raise Stop(1, f"That's the body-only copy for artifacts. Publish {path[:-len('.artifact.html')]}.html instead.")
    if path.endswith(".draft.html"):
        raise Stop(1, "That's a draft, which has no revision. Build without --draft, then publish.")


def checked_page(path):
    data = read_file(path, "page")
    if not data[:64].lstrip().lower().startswith(b"<!doctype"):
        raise Stop(1, f"{path} isn't a complete page. Publish the .html that build.py writes.")
    if b'id="pt-' not in data:
        warn("this is a review page, not a prototype. Notes left on the site won't reach it; review pages stay on artifacts for now.")
    return data


def job_bundle(a):
    folder = job_folder(a.job)
    status = read_json(os.path.join(folder, "status.json")) or {}
    info = read_json(os.path.join(folder, "wireframes.json")) or {}
    page = os.path.join(folder, "wireframes.html")
    if not os.path.isfile(page):
        raise Stop(1, f"{a.job} has no wireframes.html yet.")
    ticket = a.ticket or job_ticket(status, a.job)
    title = a.title or status.get("title") or (status.get("ticket") or {}).get("title") or info.get("title") or a.job
    source = info.get("source")
    stem = page_stem(source) if source else None
    requirements = None
    if not a.requirements:
        spec = find_spec(status, folder)
        requirements = fr_table(read_text(spec, "spec")) if spec else None
        if spec and not requirements:
            warn(f"no FR rows in {spec}, so no requirements were sent")
    decisions = os.path.join(folder, "decisions.md")
    return {"page": page, "stem": stem, "info": info, "version": info.get("version"), "title": title, "ticket": ticket,
            "ticket_url": a.ticket_url or (status.get("ticket") or {}).get("url"), "job_slug": a.job,
            "pdf": a.pdf or newest(os.path.join(folder, "*.pack.pdf")), "requirements": requirements,
            "decisions": decisions if not a.decisions and os.path.isfile(decisions) else a.decisions}


def page_bundle(a):
    page = os.path.expanduser(a.page)
    checked_name(page)
    stem = page_stem(page)
    info = read_json(stem + ".json")
    if not isinstance(info, dict) or not info.get("revision"):
        raise Stop(1, f"No {os.path.basename(stem)}.json with a revision beside the page. Publish a page that build.py wrote.")
    pdf = stem + ".pack.pdf"
    return {"page": page, "stem": stem, "info": info, "version": info["revision"], "title": a.title or info.get("title") or os.path.basename(stem),
            "ticket": a.ticket, "ticket_url": a.ticket_url, "job_slug": None, "pdf": a.pdf or (pdf if os.path.isfile(pdf) else None),
            "requirements": None, "decisions": a.decisions}


# ---------- publish ----------

def publish(a, cfg, problem, site):
    if a.ticket and not TICKET_RE.match(a.ticket):
        raise Stop(1, f"{a.ticket} isn't a ticket key. It looks like ORBIT-296.")
    b = job_bundle(a) if a.job else page_bundle(a)
    if not b["version"]:
        raise Stop(1, "wireframes.json has no version. Build the page again.")
    ticket = b["ticket"].upper() if b["ticket"] else None
    path = state_file(a)
    state = read_json(path) or {}
    key = settled_key(a, state, make_key(b["title"], ticket))

    page = checked_page(b["page"])
    pdf = read_file(os.path.expanduser(b["pdf"]), "PDF") if b["pdf"] else None
    if b["pdf"] and os.path.getmtime(os.path.expanduser(b["pdf"])) < os.path.getmtime(b["page"]):
        warn("the PDF is older than the page, so it may show an earlier revision. Build with --pack for a fresh one.")
    requirements = read_text(os.path.expanduser(a.requirements), "requirements") if a.requirements else b["requirements"]
    decisions = read_text(os.path.expanduser(b["decisions"]), "decisions") if b["decisions"] else None
    manifest = make_manifest(b["info"], b["stem"], b["version"])
    changes = a.changes or next((h.get("note") for h in manifest["history"] if h.get("rev") == b["version"]), "") or ""

    fields = {"key": key, "title": b["title"], "page_version": str(b["version"]), "manifest": json.dumps(manifest)}
    extra = {"ticket_key": ticket, "ticket_url": b["ticket_url"], "job_slug": b["job_slug"], "changes": changes, "requirements": requirements, "decisions": decisions}
    fields.update({k: v for k, v in extra.items() if v and v.strip()})
    files = {"page": ("page.html", "text/html; charset=utf-8", page)}
    if pdf:
        files["pdf"] = ("pack.pdf", "application/pdf", pdf)
    body, ctype = multipart(fields, files)

    too_big = [f"The {name} is {size(n)}; the site takes {size(LIMITS[name])}." for name, n in
               (("page", len(page)), ("pdf", len(pdf or b"")), ("requirements", len((requirements or "").encode("utf-8"))), ("decisions", len((decisions or "").encode("utf-8")))) if n > LIMITS[name]]
    if len(body) > BODY_LIMIT and not is_local(site):
        too_big.append(f"All together this is {size(len(body))}, and the site takes {size(BODY_LIMIT)} in one request. A smaller PDF would fit.")

    if a.dry_run:
        rows = [("site", site), ("key", f"{key} ({'kept' if state.get('key') else 'new'})"), ("title", b["title"]), ("ticket", ticket or "none"),
                ("ticket url", b["ticket_url"] or "none"), ("job", b["job_slug"] or "none"), ("page version", b["version"]),
                ("changes", changes or "none"), ("page", f"{b['page']}  {size(len(page))}"),
                ("pdf", f"{b['pdf']}  {size(len(pdf))}" if pdf else "none"),
                ("manifest", f"{size(len(fields['manifest']))}: {len(manifest['screens'])} screens, {len(manifest['choices'])} choices, {len(manifest['history'])} history rows"),
                ("requirements", f"{len(re.findall(FR_ROW.pattern, requirements, re.M))} FR rows, {size(len(requirements.encode('utf-8')))}" if requirements else "none"),
                ("decisions", f"{b['decisions']}  {size(len(decisions.encode('utf-8')))}" if decisions else "none"),
                ("total", size(len(body))), ("token", problem or "found, not shown"), ("remembered in", path)]
        print("Dry run: nothing was sent.")
        for label, value in rows:
            print(f"{label + ':':<15}{value}")
    if too_big:
        raise Stop(1, " ".join(too_big))
    if a.dry_run:
        return
    if problem:
        raise Stop(3, problem)

    reply = call(site, cfg["token"], "POST", "/api/publish", body, ctype, missing="This site has no publish route. Check the site address.")
    if not isinstance(reply.get("revision"), int) or not reply.get("url"):
        raise Stop(4, "The site didn't say which revision it made, so nothing was recorded here.")
    kept = {k: v for k, v in state.items() if k == "last_pull" and state.get("site") == site}
    write_json(path, {**kept, "key": key, "site": site, "url": reply["url"], "revision": reply["revision"],
                      "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    print(json.dumps(reply) if a.json else f"Published revision {reply['revision']}: {reply['url']}")


# ---------- notes ----------

def note_line(n, latest):
    """One note in the page's own feedback format: s-<id> (<device>, at "<label>", on r<n>): <word>: <text>."""
    screen = one_line(n.get("screen")) or "overview"
    screen = screen if screen.startswith("s-") or screen == "overview" else f"s-{screen}"  # the page's ids have no s-; the site's do
    where = [one_line(n.get("device"))]
    label = one_line((n.get("pin") or {}).get("label")).replace('"', "'")
    if label:
        where.append(f'at "{label}"')
    revision = n.get("revision")
    if isinstance(revision, int) and isinstance(latest, int) and revision < latest:
        where.append(f"on r{revision}")
    where = ", ".join(w for w in where if w)
    return f"{screen}{f' ({where})' if where else ''}: {WORDS.get(n.get('kind'), 'note')}: {one_line(n.get('text'))}"


def when(item):
    return item.get("updated_at") or item.get("at")


def feedback_lines(reply, since):
    """Picks, then notes, oldest first. Nothing already pulled, deleted, or un-picked gets a line."""
    after = stamp(since)
    fresh = lambda x: not after or not stamp(when(x)) or stamp(when(x)) > after  # the site keeps finer times than it sends
    order = lambda x: stamp(when(x)) or datetime.min.replace(tzinfo=timezone.utc)
    latest = (reply.get("feature") or {}).get("latest_revision")
    choices = sorted((c for c in reply.get("choices") or [] if c.get("choice") and fresh(c)), key=order)
    notes = sorted((n for n in reply.get("notes") or [] if not n.get("deleted") and fresh(n)), key=order)
    return [f"Pick {one_line(c['choice'])} for {one_line(c.get('group'))}" for c in choices] + [note_line(n, latest) for n in notes]


def picks_differ(reply):
    picks = {}
    for c in reply.get("choices") or []:
        if c.get("choice"):
            picks.setdefault(c.get("group"), set()).add(c["choice"])
    return sorted(str(g) for g, chosen in picks.items() if len(chosen) > 1)


def newest_time(reply):
    items = [x for x in (reply.get("notes") or []) + (reply.get("choices") or []) if stamp(when(x))]
    return when(max(items, key=lambda x: stamp(when(x)))) if items else None


def pull_notes(a, cfg, problem, site):
    if a.since and not stamp(a.since):
        raise Stop(1, f"{a.since} isn't a time. It looks like 2026-11-05T14:30:00Z.")
    path = state_file(a)
    if not path and a.key:
        path = state_for_key(a.key)
    state = (read_json(path) if path else None) or {}
    if not state.get("key") and not a.key:
        raise Stop(1, "This hasn't been published yet, so it has no key. Publish it first, or pass --key.")
    key = settled_key(a, state)
    same_site = state.get("site") == site
    since = a.since or (state.get("last_pull") if same_site else None)
    query = f"?{urllib.parse.urlencode({'since': since})}" if since else ""
    url = f"/api/features/{urllib.parse.quote(key)}/notes{query}"
    if a.dry_run:
        print(f"Dry run: nothing was asked.\nwould ask:      GET {site}{url}\ntoken:          {problem or 'found, not shown'}\nremembered in:  {path or 'nowhere yet'}")
        return
    if problem:
        raise Stop(3, problem)

    reply = call(site, cfg["token"], "GET", url, missing=f"The site has no feature called {key}.")
    lines = feedback_lines(reply, since)
    latest = (reply.get("feature") or {}).get("latest_revision")
    for group in picks_differ(reply):
        warn(f"people picked differently on {group}; every pick is listed, oldest first")
    if a.json:
        print(json.dumps({**reply, "lines": lines, "since": since}))
    elif lines:
        print("\n".join([f"--- Screens feedback (v{latest}) ---" if latest else "--- Screens feedback ---", *lines, "--- end ---"]))
    else:
        print(f"No new notes since {since}." if since else "No notes yet.", file=sys.stderr)

    pulled = newest_time(reply)
    if not (state and same_site):
        print("This pull wasn't remembered: nothing here records this key on this site.", file=sys.stderr)
    elif pulled and (not stamp(state.get("last_pull")) or stamp(pulled) > stamp(state["last_pull"])):
        write_json(path, {**state, "last_pull": pulled})


# ---------- the pilot: an artifact's notes, copied once ----------

def unwrap(doc):
    """(id, fields, updatedAt): the artifact data tool wraps each document; a hand-made file may not."""
    if not isinstance(doc, dict):
        return None, {}, None
    fields = doc["data"] if isinstance(doc.get("data"), dict) else doc
    return doc.get("id"), fields, doc.get("updatedAt") or fields.get("updatedAt")


def carried_pin(pin):
    """An artifact's pin is in pixels, and a pixel can't become a fraction without the screen's size."""
    if not isinstance(pin, dict):
        return None
    if "s" not in pin:
        return pin
    return {**({"label": pin["label"]} if pin.get("label") else {}), "px": {k: pin.get(k) for k in ("x", "y", "s")}}


def import_payload(data):
    """(notes, choices, skipped lines) from an export. See reference/publish.md for the file's shape."""
    names = data.get("names") if isinstance(data.get("names"), dict) else {}
    notes, choices, skipped = [], [], []
    for doc in data.get("feedback") or []:
        doc_id, f, _ = unwrap(doc)
        if not one_line(f.get("text")) or f.get("kind") not in WORDS or not stamp(f.get("at")):
            skipped.append(f"note {doc_id}: it needs text, a kind and a time")
            continue
        screen = one_line(f.get("screen"))
        notes.append({"screen": screen if screen.startswith("s-") else f"s-{screen}", "device": f.get("device"), "kind": f["kind"], "text": f["text"],
                      "pin": carried_pin(f.get("pin")), "at": f["at"], "by_label": one_line(names.get(f.get("author"))) or UNNAMED})
    for doc in data.get("notes") or []:
        doc_id, f, updated = unwrap(doc)
        group = f.get("section") or doc_id
        if group != "_meta" and f.get("choice"):
            choices.append({"group": group, "choice": f["choice"], "at": updated, "by_label": UNNAMED})  # the artifact never recorded who picked
    return notes, choices, skipped


def import_notes(a, cfg, problem, site):
    path = state_file(a)
    state = (read_json(path) if path else None) or {}
    key = settled_key(a, state)
    data = read_json(os.path.expanduser(a.import_notes))
    if not isinstance(data, dict) or not (isinstance(data.get("feedback"), list) or isinstance(data.get("notes"), list)):
        raise Stop(1, f"{a.import_notes} needs a feedback list, a notes list, or both. See reference/publish.md.")
    notes, choices, skipped = import_payload(data)
    for line in skipped:
        warn(f"left out {line}")
    unnamed = sum(n["by_label"] == UNNAMED for n in notes)
    if unnamed:
        warn(f"{unnamed} of {len(notes)} notes have no name in the file's names list; they'll say \"{UNNAMED}\"")
    if a.dry_run:
        print(f"Dry run: nothing was sent.\nwould add:      {len(notes)} notes and {len(choices)} choices to {key} on {site}\nleft out:       {len(skipped)}\n"
              f"token:          {problem or 'found, not shown'}\nAnything already on the site is left out when this runs for real.")
        return
    if problem:
        raise Stop(3, problem)

    notes_url = f"/api/features/{urllib.parse.quote(key)}/notes"
    missing = f"The site has no feature called {key}. Publish the page first."
    there = call(site, cfg["token"], "GET", notes_url, missing=missing)
    seen = {(stamp(n.get("at")), n.get("text")) for n in there.get("notes") or []}
    seen_picks = {(c.get("group"), c.get("choice")) for c in there.get("choices") or []}
    new_notes = [n for n in notes if (stamp(n["at"]), n["text"]) not in seen]
    new_choices = [c for c in choices if (c["group"], c["choice"]) not in seen_picks]
    if not new_notes and not new_choices:
        print(f"Nothing new to import: all {len(notes)} notes and {len(choices)} choices are on the site already.", file=sys.stderr)
        return
    body = json.dumps({"notes": new_notes, "choices": new_choices}).encode("utf-8")
    reply = call(site, cfg["token"], "POST", notes_url, body, "application/json", missing=missing)
    if reply.get("notes") != len(new_notes) or reply.get("choices") != len(new_choices):
        raise Stop(4, f"Sent {len(new_notes)} notes and {len(new_choices)} choices, but the site says it took {reply.get('notes')} and {reply.get('choices')}.")
    print(json.dumps(reply) if a.json else f"Imported {len(new_notes)} notes and {len(new_choices)} choices to {key}. {len(notes) - len(new_notes)} notes were there already.")


def main():
    ap = argparse.ArgumentParser(description="Publish a prototype to the prototypes site, and bring its notes back. See reference/publish.md.")
    ap.add_argument("--job", help="A /feature job's slug")
    ap.add_argument("--page", help="A built page, <slug>.html, outside any job")
    ap.add_argument("--notes", action="store_true", help="Print new notes as the Foreman's feedback lines")
    ap.add_argument("--since", help="With --notes: from this time, instead of the last pull")
    ap.add_argument("--import-notes", metavar="JSON", help="Copy an artifact's notes to the site, once")
    ap.add_argument("--title", help="The feature's title")
    ap.add_argument("--key", help="The feature's key: used once, then kept")
    ap.add_argument("--ticket", help="Ticket key, such as ORBIT-296")
    ap.add_argument("--ticket-url", help="Link to the ticket")
    ap.add_argument("--requirements", help="Markdown file to send as the requirements")
    ap.add_argument("--decisions", help="Markdown file to send as the decisions")
    ap.add_argument("--pdf", help="PDF to send, instead of the one beside the page")
    ap.add_argument("--changes", help="One line on what changed in this revision")
    ap.add_argument("--site", help="Use this site instead of the one in ~/.claude/prototypes.json")
    ap.add_argument("--dry-run", action="store_true", help="Say what would be sent, and send nothing")
    ap.add_argument("--json", action="store_true", help="Print the site's reply as JSON")
    a = ap.parse_args()
    if a.job and a.page:
        ap.error("pass --job or --page, not both")
    if a.notes and a.import_notes:
        ap.error("pass --notes or --import-notes, not both")
    if a.since and not a.notes:
        ap.error("--since goes with --notes")
    if a.notes and not (a.job or a.page or a.key):
        ap.error("--notes needs --job, --page or --key")
    if a.import_notes and not (a.job or a.page or a.key):
        ap.error("--import-notes needs --key")
    if not (a.notes or a.import_notes or a.job or a.page):
        ap.error("pass --job or --page to publish, or --notes, or --import-notes")
    try:
        cfg, problem = load_config()
        site = pick_site(a.site, cfg)
        (pull_notes if a.notes else import_notes if a.import_notes else publish)(a, cfg, problem, site)
    except Stop as e:
        print(e, file=sys.stderr)
        sys.exit(e.code)


if __name__ == "__main__":
    main()
