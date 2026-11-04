#!/usr/bin/env python3
"""Fill template.html for the current branch.

Usage: python3 build.py --title "Optional rating comments" --sections sections.html
                       [--base moxie/main] [--pr 76 | --pr https://github.com/OWNER/REPO/pull/76] [--mode quick|full]

Works out the branch, SHA, base, PR, push state, file list and diff link from git,
writes ~/.claude/review-walkthroughs/<repo>/<branch-slug>.html and prints that path
plus the saved artifact URL (if this branch already has one).

--pr points the header, Diff button, file links and {{BLOB}} at that PR's repository and
head commit, even when the local checkout is a fork or a pre-merge commit. The file list
still comes from the local diff against the merge-base with --base.

In the sections file, {{BLOB}} becomes https://github.com/OWNER/REPO/blob/<head sha>.
"""
import argparse, html, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def git(*args, check=True):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def gh_repo(remote):
    url = git("remote", "get-url", remote, check=False)
    m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", url)
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True, help='Feature name; " walkthrough" is added')
    ap.add_argument("--sections", required=True, help="File with the <section> blocks")
    ap.add_argument("--base", help="Base ref (default: moxie/main, upstream/main or origin/main)")
    ap.add_argument("--pr", help="PR number or URL to link to (default: the PR for the current branch, if any)")
    ap.add_argument("--mode", choices=["quick", "full"], default="quick", help="Mode the page opens in the first time")
    a = ap.parse_args()

    os.chdir(git("rev-parse", "--show-toplevel"))
    repo = os.path.basename(os.getcwd())
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    sha = git("rev-parse", "HEAD")
    remotes = git("remote").split()
    base = a.base or next((f"{r}/main" for r in ("moxie", "upstream", "origin") if r in remotes), None)
    if not base:
        sys.exit("No base branch found; pass --base")
    mb = git("merge-base", "HEAD", base)

    # Where the commit is pushed decides whether file links can work.
    pushed_on = [l.strip().split("/")[0] for l in git("branch", "-r", "--contains", "HEAD", check=False).splitlines() if l.strip() and "->" not in l]
    remote = "origin" if "origin" in pushed_on else (pushed_on[0] if pushed_on else None)
    owner_repo = gh_repo(remote) if remote else None

    pr = None
    cmd = ["gh", "pr", "view"]
    if a.pr:
        m = re.search(r"github\.com/([^/]+/[^/]+)/pull/(\d+)", a.pr)
        cmd += [m.group(2), "--repo", m.group(1)] if m else [a.pr]
    r = subprocess.run(cmd + ["--json", "number,url,state,headRefOid,headRefName,baseRefName"], capture_output=True, text=True)
    if r.returncode == 0:
        try:
            pr = json.loads(r.stdout)
        except ValueError:
            pass
    elif a.pr:
        sys.exit(f"gh pr view {a.pr} failed: {r.stderr.strip()}")

    # Links: the PR's own repository and head commit when there is a PR, else where HEAD is pushed.
    link_sha, base_label = sha, base
    if pr:
        owner_repo = re.search(r"github\.com/([^/]+/[^/]+)/pull/", pr["url"]).group(1)
        link_sha, base_label = pr["headRefOid"], pr["baseRefName"]
        branch = pr["headRefName"]
        if link_sha != sha:
            print(f"note: local HEAD {sha[:8]} is not the PR head {link_sha[:8]}; files come from the local diff, links from the PR head")

    where = (f'<a href="{pr["url"]}">PR #{pr["number"]}</a>' if pr
             else "on the fork, no PR yet" if owner_repo else "not pushed yet")
    meta = f"Branch <code>{html.escape(branch)}</code> · <code>{link_sha[:7]}</code> · {where} · vs <code>{html.escape(base_label)}</code>"

    if pr:
        diff_link = f'<a class="btn" href="{pr["url"]}/files">Diff</a>'
    elif owner_repo:
        diff_link = f'<a class="btn" href="https://github.com/{owner_repo}/compare/{mb}...{sha}">Diff</a>'
    else:
        diff_link = ""

    rows = []
    for line in git("diff", "--numstat", f"{mb}..HEAD").splitlines():
        add, dele, path = line.split("\t", 2)
        if "=>" in path:  # rename: keep the new path
            path = re.sub(r"\{(.*?) => (.*?)\}", r"\2", path).split(" => ")[-1]
        if path.endswith(("lock.json", ".lock", "pnpm-lock.yaml")):
            continue
        exists = os.path.exists(path)
        ref = link_sha if exists else mb
        label = html.escape(path)
        n = f'<span class="n"><span class="add">+{add}</span> <span class="del">−{dele}</span></span>' if add != "-" else '<span class="n">binary</span>'
        if owner_repo:
            rows.append(f'            <a href="https://github.com/{owner_repo}/blob/{ref}/{path}" data-file="{label}"><span class="path">{label}</span>{n}</a>')
        else:
            rows.append(f'            <a data-file="{label}"><span class="path">{label}</span>{n}</a>')

    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", branch).strip("-")
    page = open(os.path.join(HERE, "template.html")).read()
    sections = open(os.path.expanduser(a.sections)).read()
    if "{{BLOB}}" in sections:
        if not owner_repo:
            sys.exit("Sections use {{BLOB}} but the commit is not pushed; use <code data-file> chips without links")
        sections = sections.replace("{{BLOB}}", f"https://github.com/{owner_repo}/blob/{link_sha}")
    for k, v in {
        "{{TITLE}}": f"{a.title} walkthrough",
        "{{META}}": meta,
        "{{DIFF_LINK}}": diff_link,
        "{{FILE_COUNT}}": str(len(rows)),
        "{{FILES}}": "\n".join(rows),
        "{{NOTES_KEY}}": f"rw-{repo}-{slug}-notes",
        "{{SECTIONS}}": sections,
        "{{DEFAULT_MODE}}": a.mode,
    }.items():
        page = page.replace(k, v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", page)
    if left:
        sys.exit(f"Unfilled placeholders: {left}")

    out_dir = os.path.expanduser(f"~/.claude/review-walkthroughs/{repo}")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{slug}.html")
    open(out, "w").write(page)
    url_file = os.path.join(out_dir, f"{slug}.url")
    print(f"file: {out}")
    print(f"github: {owner_repo or '(not pushed)'} @ {link_sha}")
    print(f"artifact: {open(url_file).read().strip() if os.path.exists(url_file) else '(new, save the URL to ' + url_file + ')'}")


if __name__ == "__main__":
    main()
