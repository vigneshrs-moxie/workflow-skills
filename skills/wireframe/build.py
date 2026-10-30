#!/usr/bin/env python3
"""Build a wireframe review page from <section> blocks.

Usage: python3 build.py --title "Invoice CSV export" --sections sections.html
                       [--fidelity sketch|lo|hi] [--theme theme.css | --preset admin|consumer|mono]
                       [--fonts "Geist,Geist Mono"] [--sources sources.txt] [--job <slug>] [--slug <name>]

Run it from the repository the screens were drawn from (or anywhere, for an idea with no
repository). It writes, under ~/.claude/wireframes/<repo or "ideas">/:
  <slug>.html           the review page as a complete document: open it from disk
  <slug>.artifact.html  the same page, body only: what the Artifact tool publishes
  <slug>.brief.md       the build brief: screens, states, exits, callouts, choices, questions
  <slug>.json           revision counter, tier, artifact URL
and keeps ~/.claude/wireframes/index.html (+ manifest.js), a gallery of every page built.

Fidelity: "lo" (default) draws with the greyscale kit; "sketch" draws the same kit in a
hand-drawn style; "hi" needs --theme (the app's own CSS, see reference/design-capture.md) or
--preset (a bundled design, for ideas with no design system). Hi-fi pages compile Tailwind in
the browser and load Lucide icons, so .frame.hifi screens can use the app's own classes.

With --job <slug> (inside a /feature job) it also writes to the job's private folder
($STARBASE_FEATURES_DIR, else the older $WORKSHOP_FEATURES_DIR, else ~/.claude/feature-work, then <slug>/):
  wireframes.html      the page as a complete document, viewable straight from disk
  wireframes.json      screens, choices, questions, exits, tier, revision ("version"), URL
  wireframes.brief.md  the build brief
After publishing, record the link (same --slug or --title, and --job if any):
  python3 build.py --record-url <artifact url> --title "Invoice CSV export" [--job <slug>]

--draft writes only <slug>.draft.html, for looking at the page while you work on it; the revision,
the brief, the job files and the gallery are untouched until a build without it.

Design cache (hi-fi): the capture of an app's design lives at ~/.claude/wireframes/<repo>/design.md
with its theme.css. `--design-check` says whether the files it was captured from have changed;
`--design-stamp` records their current hashes after you write or update it.

Checks before writing: unique keys, an <h2> per section, pins 1..n matching callouts, two
options per design choice, data-go targets that exist, an exit per screen, an empty state for
screens with a table, no lorem ipsum, and a theme for hi-fi frames.
"""
import argparse, hashlib, html, json, os, re, subprocess, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
# Pinned versions of the in-page Tailwind compiler and the icon set.
TAILWIND = "https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4.1.11"
LUCIDE = "https://cdn.jsdelivr.net/npm/lucide@0.469.0/dist/umd/lucide.min.js"
PRESET_FONTS = {"admin": "IBM Plex Sans", "consumer": "Nunito Sans", "mono": "Geist"}
SKETCH_FONTS = "Patrick Hand,Caveat"
TIERS = {
    "sketch": ("Sketch", "Hand-drawn: structure, flow and wording. Nothing about looks is decided."),
    "lo": ("Lo-fi", "Greyscale boxes: layout, content and wording. Colours and type are not decided."),
    "hi": ("Hi-fi", "The app's own design: what it will look like when built."),
    "preset": ("Hi-fi · preset", "A bundled design standing in for the app's: layout, content and wording are decided; the look is a placeholder."),
}
HOME = os.path.join(os.path.expanduser("~"), ".claude", "wireframes")


def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout.strip() if r.returncode == 0 else None


def blocks(sections):
    """(key, attrs, block) for every <section data-key>."""
    out = []
    for b in re.split(r"(?=<section\b)", sections):
        tag = re.match(r"<section\b[^>]*>", b)
        if not tag:
            continue
        attrs = dict(re.findall(r"([\w-]+)=\"([^\"]*)\"", tag.group(0)))
        for flag in ("data-choice", "data-end"):
            if re.search(r"\b" + flag + r"\b", tag.group(0)):
                attrs.setdefault(flag, "")
        if attrs.get("data-key"):
            out.append((attrs["data-key"], attrs, b))
    return out


def text(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", h))).strip()


def exits(block):
    """[(label, target)] for every data-go hotspot in a block, in order."""
    out = []
    for m in re.finditer(r"<([a-z][\w-]*)\b([^>]*)\bdata-go=\"([^\"]+)\"([^>]*)>", block):
        tag, before, target, after = m.groups()
        label = re.search(r"data-go-label=\"([^\"]*)\"", before + after)
        if label:
            label = html.unescape(label.group(1))
        else:
            rest = block[m.end():]
            inner = re.search(r"</" + tag + r">", rest)
            chunk = rest[: inner.start()] if inner else rest[:200]
            label = text(re.sub(r"<i class=\"pin\">\s*\d+\s*</i>", "", chunk))[:60]
        out.append((label or target, target))
    return out


def states_of(block):
    return re.findall(r"class=\"state\"[^>]*data-label=\"([^\"]*)\"", block) or \
        [text(c) for c in re.findall(r"<figcaption[^>]*>(.*?)</figcaption>", block, re.S)]


def check(sections):
    """Return (errors, warnings) for the sections file."""
    errors, warnings, keys = [], [], []
    if re.search(r"lorem\s+ipsum", sections, re.I):
        errors.append("lorem ipsum found: write real labels and plausible invented data")
    EMPTY = r"\bempty\b|no (matches|results|rows|items)|nothing (to|matches|here)"
    seen_empty = False  # an empty state drawn on an earlier screen covers the same table later in the flow
    for key, attrs, b in blocks(sections):
        if key in keys:
            errors.append(f"data-key \"{key}\" is used twice")
        keys.append(key)
        if "<h2" not in b:
            errors.append(f"{key}: no <h2>")
        drawn = re.sub(r"<div class=\"legend\">.*?</div>", "", b, flags=re.S)  # the legend's sample pin isn't a pin
        pins = [int(n) for n in re.findall(r"class=\"pin[^\"]*\"[^>]*>\s*(\d+)\s*<", drawn)]
        callouts = re.search(r"<ol class=\"callouts\">(.*?)</ol>", b, re.S)
        count = len(re.findall(r"<li\b", callouts.group(1))) if callouts else 0
        if pins and sorted(set(pins)) != list(range(1, count + 1)):
            warnings.append(f"{key}: pins {sorted(set(pins))} don't match {count} callouts")
        if count and not pins:
            warnings.append(f"{key}: {count} callouts but no pins in the wireframe")
        if "data-choice" in attrs:
            n = len(re.findall(r"class=\"option[\" ]", b))
            if n != 2:
                errors.append(f"{key}: a design choice needs exactly 2 options, found {n}")
        if "data-screen" in attrs:
            if not exits(b) and "data-end" not in attrs:
                warnings.append(f"{key}: no exit. Put data-go=\"<section key>\" on the control that leaves this screen, or data-end on the section if the flow ends here")
            has_table = bool(re.search(r"<table\b|class=\"wt\"", b))
            drawn_empty = bool(re.search(EMPTY, " ".join(states_of(b)).lower()) or re.search(r"class=\"[^\"]*\bempty\b", b))
            said = bool(re.search(EMPTY, (callouts.group(1) if callouts else "").lower()))
            if has_table and not drawn_empty and not said and not seen_empty:
                warnings.append(f"{key}: a table with no empty state. Add a state tab for it, or say in a callout why it can't be empty")
            seen_empty = seen_empty or drawn_empty
    for m in re.finditer(r"data-go=\"([^\"]+)\"", sections):
        if m.group(1) not in keys:
            errors.append(f"data-go=\"{m.group(1)}\" points at no section")
    if not keys:
        errors.append("no <section data-key> blocks found")
    return errors, warnings


def summary(sections):
    """What the page holds, for the brief, the Foreman and Starbase."""
    out = {"screens": [], "choices": [], "questions": []}
    for key, attrs, b in blocks(sections):
        h2 = re.search(r"<h2[^>]*>(.*?)</h2>", b, re.S)
        if "data-screen" in attrs:
            out["screens"].append({"key": key, "name": attrs["data-screen"], "states": states_of(b),
                                   "exits": [{"label": l, "to": t} for l, t in exits(b)], "end": "data-end" in attrs})
        elif "data-choice" in attrs:
            opts = []
            for o in re.split(r"(?=<figure class=\"option)", b)[1:]:
                oa = dict(re.findall(r"([\w-]+)=\"([^\"]*)\"", re.match(r"<figure[^>]*>", o).group(0)))
                opts.append({"id": oa.get("data-option"), "label": html.unescape(oa.get("data-label", "")), "recommended": 'class="rec"' in o})
            out["choices"].append({"key": key, "question": text(h2.group(1)) if h2 else "", "options": opts})
        elif key == "questions":
            for li in re.findall(r"<li\b[^>]*>(.*?)</li>", b, re.S):
                kind = "assumed" if "flag assume" in li else "decide"
                out["questions"].append({"kind": kind, "text": re.sub(r"^(Decide|Assumed)\s*", "", text(li))})
    return out


def brief(title, tier, where, sources, sections, info):
    """The build brief: what an implementer needs from the page, as Markdown."""
    by_key = {k: (a, b) for k, a, b in blocks(sections)}
    names = {}
    for k, (a, b) in by_key.items():
        h2 = re.search(r"<h2[^>]*>(.*?)</h2>", b, re.S)
        names[k] = a.get("data-screen") or (text(h2.group(1)) if h2 else k)
    L = [f"# {title} · build brief", "", f"{TIERS[tier][0]} screens. {where}.", ""]
    if sources:
        L += ["## Based on", ""] + [f"- `{s}`" for s in sources] + [""]
    if "overview" in by_key:
        lede = re.search(r"<p class=\"lede\">(.*?)</p>", by_key["overview"][1], re.S)
        if lede:
            L += ["## What it adds", "", text(lede.group(1)), ""]
    L += ["## Screens", ""]
    for i, s in enumerate(info["screens"], 1):
        a, b = by_key[s["key"]]
        ctx = re.search(r"</h2>\s*<p>(.*?)</p>", b, re.S)
        L.append(f"### {i}. {s['name']}")
        if ctx:
            L.append(text(ctx.group(1)))
        if s["states"]:
            L.append("- States: " + " · ".join(s["states"]))
        new = []
        for m in re.finditer(r"<([a-z][\w-]*)\b[^>]*class=\"[^\"]*\bnew\b[^\"]*\"[^>]*>", b):
            rest = b[m.end():]
            close = re.search(r"</" + m.group(1) + r">", rest)
            label = text(re.sub(r"<i class=\"pin\">\s*\d+\s*</i>", "", rest[: close.start()] if close else rest[:120]))[:50]
            if label and label not in new:
                new.append(label)
        if new:
            L.append("- New here: " + "; ".join(new[:8]))
        if s["exits"]:
            L.append("- Exits: " + "; ".join(f"{e['label']} → {names.get(e['to'], e['to'])}" for e in s["exits"]))
        elif s["end"]:
            L.append("- The flow ends here.")
        callouts = re.search(r"<ol class=\"callouts\">(.*?)</ol>", b, re.S)
        for j, li in enumerate(re.findall(r"<li\b[^>]*>(.*?)</li>", callouts.group(1) if callouts else "", re.S), 1):
            L.append(f"- ({j}) {text(li)}")
        L.append("")
    if info["choices"]:
        L += ["## Design choices", ""]
        for c in info["choices"]:
            a, b = by_key[c["key"]]
            parts = re.split(r"(?=<figure class=\"option)", b)[1:]
            L.append(f"### {c['question']}")
            for o, part in zip(c["options"], parts):
                t = re.search(r"<h5>Good</h5>\s*<ul>(.*?)</ul>", part, re.S)
                w = re.search(r"<h5>Watch</h5>\s*<ul>(.*?)</ul>", part, re.S)
                good = "; ".join(text(x) for x in re.findall(r"<li>(.*?)</li>", t.group(1), re.S)) if t else ""
                watch = "; ".join(text(x) for x in re.findall(r"<li>(.*?)</li>", w.group(1), re.S)) if w else ""
                L.append(f"- **{o['id']}. {o['label']}**{' (recommended)' if o['recommended'] else ''}" +
                         (f". Good: {good}" if good else "") + (f". Watch: {watch}" if watch else ""))
            L.append("")
    if info["questions"]:
        L += ["## To settle", ""] + [f"- {'Decide' if q['kind'] == 'decide' else 'Assumed'}: {q['text']}" for q in info["questions"]] + [""]
    L += ["## When reviewed", "", "Picks, verdicts and notes come back from the page (Copy feedback, or the artifact's `notes` collection). Record the decisions under \"To settle\" in the next revision, and build only what was picked.", ""]
    return "\n".join(L)


def sha(path):
    try:
        return hashlib.sha1(open(path, "rb").read()).hexdigest()[:12]
    except OSError:
        return None


def design_sources(design_md):
    """[(path, hash)] from the design.md frontmatter."""
    fm = re.match(r"---\n(.*?)\n---", design_md, re.S)
    if not fm:
        return []
    out = []
    for line in fm.group(1).splitlines():
        m = re.match(r"\s*-\s+(\S+)(?:\s+([0-9a-f]{6,40}))?\s*$", line)
        if m:
            out.append((m.group(1), m.group(2) or ""))
    return out


def design_check(top, out_dir):
    path = os.path.join(out_dir, "design.md")
    if not os.path.exists(path):
        print(f"design: none ({path})")
        return 2
    srcs = design_sources(open(path, encoding="utf-8").read())
    changed = [p for p, h in srcs if sha(os.path.join(top or ".", p)) != h]
    if changed:
        print(f"design: stale, changed since capture: {', '.join(changed)} ({path})")
        return 1
    print(f"design: fresh, {len(srcs)} source files unchanged ({path})")
    return 0


def design_stamp(top, out_dir):
    path = os.path.join(out_dir, "design.md")
    if not os.path.exists(path):
        sys.exit(f"no design.md at {path}")
    md = open(path, encoding="utf-8").read()
    fm = re.match(r"---\n(.*?)\n---", md, re.S)
    if not fm:
        sys.exit("design.md needs a frontmatter block with a sources: list (see reference/design-capture.md)")
    lines, n = [], 0
    for line in fm.group(1).splitlines():
        m = re.match(r"(\s*-\s+)(\S+)(?:\s+[0-9a-f]{6,40})?\s*$", line)
        if m:
            h = sha(os.path.join(top or ".", m.group(2)))
            if h is None:
                sys.exit(f"design.md lists {m.group(2)} but the file isn't there")
            line = f"{m.group(1)}{m.group(2)} {h}"
            n += 1
        lines.append(line)
    open(path, "w", encoding="utf-8").write(md[: fm.start(1)] + "\n".join(lines) + md[fm.end(1):])
    print(f"design: stamped {n} source files in {path}")


def gallery(entry):
    """Keep ~/.claude/wireframes/index.html and manifest.js, one line per page, newest last."""
    os.makedirs(HOME, exist_ok=True)
    mpath = os.path.join(HOME, "manifest.js")
    lines = []
    if os.path.exists(mpath):
        for line in open(mpath, encoding="utf-8"):
            m = re.match(r"window\.WIREFRAMES\.push\((\{.*\})\);\s*$", line)
            if m:
                try:
                    old = json.loads(m.group(1))
                except ValueError:
                    continue
                if (old.get("repo"), old.get("slug")) != (entry["repo"], entry["slug"]):
                    lines.append(line.rstrip("\n"))
    lines.append("window.WIREFRAMES.push(" + json.dumps(entry) + ");")
    open(mpath, "w", encoding="utf-8").write("window.WIREFRAMES = window.WIREFRAMES || [];\n" + "\n".join(lines) + "\n")
    index = os.path.join(HOME, "index.html")
    src = os.path.join(HERE, "gallery.html")
    if os.path.exists(src):
        open(index, "w", encoding="utf-8").write(open(src, encoding="utf-8").read())
    return index


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", help="Feature name, as the page title")
    ap.add_argument("--sections", help="File with the <section> blocks")
    ap.add_argument("--fidelity", choices=["sketch", "lo", "hi"], help="Default: hi with --theme or --preset, otherwise lo")
    ap.add_argument("--theme", help="The app's CSS for hi-fi screens (see reference/design-capture.md)")
    ap.add_argument("--preset", choices=sorted(PRESET_FONTS), help="A bundled design instead of --theme, for ideas with no design system")
    ap.add_argument("--fonts", help='Comma-separated Google Fonts families, e.g. "Geist,Geist Mono"')
    ap.add_argument("--sources", help="File listing the repository files read, one per line")
    ap.add_argument("--job", help="Feature slug: also write wireframes.html/.json/.brief.md to the job folder")
    ap.add_argument("--slug", help="Output name (default: from the title)")
    ap.add_argument("--draft", action="store_true", help="Build <slug>.draft.html to look at, without bumping the revision or touching the job files, brief or gallery")
    ap.add_argument("--record-url", help="Only save this published artifact URL for the page (no build)")
    ap.add_argument("--design-check", action="store_true", help="Say whether the cached design.md is fresh (exit 0), stale (1) or missing (2)")
    ap.add_argument("--design-stamp", action="store_true", help="Record the current hashes of the files design.md lists")
    a = ap.parse_args()

    top = git("rev-parse", "--show-toplevel")
    repo = os.path.basename(top) if top else "ideas"
    branch = git("rev-parse", "--abbrev-ref", "HEAD") if top else None
    out_dir = os.path.join(HOME, repo)
    if a.design_check:
        sys.exit(design_check(top, out_dir))
    if a.design_stamp:
        design_stamp(top, out_dir)
        return

    if not (a.slug or a.title):
        sys.exit("pass --title (or --slug)")
    slug = a.slug or re.sub(r"[^a-z0-9]+", "-", a.title.lower()).strip("-")
    job_dir = None
    if a.job:
        root = os.path.expanduser(os.environ.get("STARBASE_FEATURES_DIR") or os.environ.get("WORKSHOP_FEATURES_DIR") or os.path.join("~", ".claude", "feature-work"))
        job_dir = os.path.join(root, a.job)
        if not os.path.isdir(job_dir):
            sys.exit(f"no feature folder at {job_dir}")
    meta_path = os.path.join(out_dir, f"{slug}.json")
    try:
        meta = json.load(open(meta_path, encoding="utf-8"))
    except (OSError, ValueError):
        meta = {}

    if a.record_url:
        if not re.match(r"https://claude\.ai/(code/)?artifact/[\w-]+$", a.record_url):
            sys.exit("--record-url takes a claude.ai artifact link")
        os.makedirs(out_dir, exist_ok=True)
        open(os.path.join(out_dir, f"{slug}.url"), "w", encoding="utf-8").write(a.record_url + "\n")
        meta["url"] = a.record_url
        open(meta_path, "w", encoding="utf-8").write(json.dumps(meta, indent=2) + "\n")
        print(f"saved: {out_dir}/{slug}.url")
        if job_dir:
            open(os.path.join(job_dir, "wireframes.url"), "w", encoding="utf-8").write(a.record_url + "\n")
            jpath = os.path.join(job_dir, "wireframes.json")
            if os.path.exists(jpath):
                info = json.load(open(jpath, encoding="utf-8"))
                info["url"] = a.record_url
                open(jpath, "w", encoding="utf-8").write(json.dumps(info, indent=2) + "\n")
            print(f"saved: {job_dir}/wireframes.url and wireframes.json")
        if meta.get("file"):
            gallery(meta)
        return
    if not (a.title and a.sections):
        sys.exit("pass --title and --sections")

    sections = open(os.path.expanduser(a.sections), encoding="utf-8").read()
    errors, warnings = check(sections)
    for w in warnings:
        print(f"warning: {w}")
    if errors:
        sys.exit("fix these first:\n  " + "\n  ".join(errors))

    # Fidelity and the theme.
    if a.theme and a.preset:
        sys.exit("pass --theme or --preset, not both")
    tier = a.fidelity or ("hi" if (a.theme or a.preset) else "lo")
    if tier == "hi" and not (a.theme or a.preset):
        sys.exit("hi-fi needs --theme <the app's CSS> or --preset admin|consumer|mono")
    if tier != "hi" and (a.theme or a.preset):
        sys.exit(f"--theme/--preset only apply to hi-fi; drop them or drop --fidelity {tier}")
    if "frame hifi" in sections and tier != "hi":
        sys.exit("Sections have hi-fi frames (.frame.hifi) but the build isn't hi-fi: pass --theme or --preset")
    if tier == "hi" and "frame hifi" not in sections:
        print("warning: hi-fi build but no .frame.hifi in the sections; the screens will draw with the lo-fi kit")
    tier_key = "preset" if a.preset else tier

    head_extra = foot_extra = ""
    fonts = a.fonts or ""
    if tier == "hi":
        theme = open(os.path.expanduser(a.theme) if a.theme else os.path.join(HERE, "presets", f"{a.preset}.css"), encoding="utf-8").read()
        if re.search(r"^\s*@import\b", theme, re.M):
            print("warning: dropped @import lines from the theme (the in-page compiler includes Tailwind itself)")
            theme = re.sub(r"^\s*@import\b[^\n]*\n", "", theme, flags=re.M)
        if re.search(r"(^|[\s,])(html|body)\s*[,{]", theme):
            print("warning: the theme styles html or body; scope those rules to .canvas or they restyle the review page")
        loose = re.findall(r"^(?:table|a|button|input|select|textarea|h[1-6]|p|ul|ol|li|label|nav|main|header|footer)\b[^{]*\{", theme, re.M)
        if loose:
            print(f"warning: the theme has {len(loose)} element rules not scoped to .canvas (e.g. {loose[0].strip()[:40]}); they restyle the review page")
        if "</style" in theme:
            sys.exit("The theme contains </style>")
        if a.preset and not fonts:
            fonts = PRESET_FONTS[a.preset]
        head_extra = f'<script src="{TAILWIND}"></script>\n<style type="text/tailwindcss">\n{theme}\n</style>'
        foot_extra = f'<script src="{LUCIDE}"></script>'
    if tier == "sketch":
        fonts = ",".join(x for x in [SKETCH_FONTS, fonts] if x)
    if fonts:
        fams = "&".join("family=" + f.strip().replace(" ", "+") + ":wght@400;500;600;700" for f in fonts.split(",") if f.strip())
        head_extra = f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{fams}&display=swap">\n' + head_extra

    sources = []
    if a.sources:
        sources = [l.strip() for l in open(os.path.expanduser(a.sources), encoding="utf-8") if l.strip()]
    if sources:
        rows = "\n".join(f"            <code>{html.escape(s)}</code>" for s in sources)
        sources_html = (
            '<details class="menu">\n'
            f'          <summary class="btn" title="The repository files these screens were drawn from">Based on ({len(sources)})</summary>\n'
            '          <div class="menu-panel">\n'
            f'            <p>Layouts, labels and patterns were taken from these files in <code style="display:inline">{html.escape(repo)}</code>.</p>\n'
            f"{rows}\n"
            "          </div>\n"
            "        </details>")
    else:
        sources_html = ""

    where = (f"Drawn from <code>{html.escape(repo)}</code> on <code>{html.escape(branch)}</code>" if top
             else "Drawn from the idea alone; no repository was read")
    label, explain = TIERS[tier_key]
    tier_html = f'<span class="tier" title="{html.escape(explain)}">{html.escape(label)}</span>'
    meta_line = f"{html.escape(explain)} · {where}"

    # One revision counter per page, shared by the standalone page and the job files.
    prev = {}
    jpath = os.path.join(job_dir, "wireframes.json") if job_dir else None
    if jpath:
        try:
            prev = json.load(open(jpath, encoding="utf-8"))
        except (OSError, ValueError):
            prev = {}
    revision = max(int(meta.get("revision", 0)), int(prev.get("version", 0))) + (0 if a.draft else 1)
    revision = max(revision, 1)

    page = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    for k, v in {
        "{{TITLE}}": f"{a.title} wireframes",
        "{{META}}": meta_line,
        "{{TIER}}": tier_html,
        "{{MODE}}": {"sketch": "sketch", "lo": "lofi", "hi": "hifi"}[tier],
        "{{SOURCES}}": sources_html,
        "{{NOTES_KEY}}": f"wf-{repo}-{slug}-notes",
        "{{VERSION}}": str(revision),
        "{{SECTIONS}}": sections,
        "{{HEAD_EXTRA}}": head_extra,
        "{{FOOT_EXTRA}}": foot_extra,
    }.items():
        page = page.replace(k, v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", page)
    if left:
        sys.exit(f"Unfilled placeholders: {left}")

    os.makedirs(out_dir, exist_ok=True)
    # Two copies: a complete document to open from disk (the gallery links to it; without a doctype a
    # browser renders in quirks mode), and the body-only file the Artifact tool wraps when publishing.
    doc = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>'
           + page + "</body></html>")
    if a.draft:
        draft = os.path.join(out_dir, f"{slug}.draft.html")
        open(draft, "w", encoding="utf-8").write(doc)
        print(f"draft: {draft}  (open this from disk; nothing else was written)")
        return
    out = os.path.join(out_dir, f"{slug}.html")
    pub = os.path.join(out_dir, f"{slug}.artifact.html")
    open(out, "w", encoding="utf-8").write(doc)
    open(pub, "w", encoding="utf-8").write(page)
    url_file = os.path.join(out_dir, f"{slug}.url")
    url = (open(url_file, encoding="utf-8").read().strip() if os.path.exists(url_file) else None) or meta.get("url")
    if job_dir and not url:
        job_url_file = os.path.join(job_dir, "wireframes.url")
        url = (open(job_url_file, encoding="utf-8").read().strip() if os.path.exists(job_url_file) else None) or prev.get("url")
    info = summary(sections)
    where_text = re.sub(r"<[^>]+>", "", where)
    brief_md = brief(a.title, tier_key, where_text, sources, sections, info)
    brief_path = os.path.join(out_dir, f"{slug}.brief.md")
    open(brief_path, "w", encoding="utf-8").write(brief_md)
    built = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    meta = {"title": a.title, "slug": slug, "repo": repo, "tier": tier_key, "revision": revision,
            "file": f"{repo}/{slug}.html", "publish": f"{repo}/{slug}.artifact.html", "brief": f"{repo}/{slug}.brief.md",
            "url": url, "built_at": built}
    open(meta_path, "w", encoding="utf-8").write(json.dumps(meta, indent=2) + "\n")
    print(f"file: {out}  (open this from disk)")
    print(f"publish: {pub}  (publish this with the Artifact tool)")
    print(f"brief: {brief_path}")
    print(f"revision: {revision}")
    if job_dir:
        open(os.path.join(job_dir, "wireframes.html"), "w", encoding="utf-8").write(doc)
        open(os.path.join(job_dir, "wireframes.brief.md"), "w", encoding="utf-8").write(brief_md)
        job_info = {"schema_version": 2, "version": revision, "title": a.title,
                    "fidelity": "high" if tier == "hi" else "low", "tier": tier_key, "url": url, "page": "wireframes.html",
                    "brief": "wireframes.brief.md", "source": out, "repo": top, "built_at": built, **info}
        open(jpath, "w", encoding="utf-8").write(json.dumps(job_info, indent=2) + "\n")
        print(f"job: {job_dir}/wireframes.html, wireframes.json and wireframes.brief.md (version {revision})")
    index = gallery(meta)
    print(f"gallery: {index}")
    print(f"artifact: {url or '(new, save the URL with --record-url)'}")


if __name__ == "__main__":
    main()
