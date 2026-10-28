#!/usr/bin/env python3
"""Read-only preflight for the three PR stages (fork -> org branch -> staging -> main).

Usage, from inside the repository checkout:
  python3 preflight.py [--stage 1|2|3|sync] [--branch <name>] [--org <owner/repo>] [--json]

It fetches both remotes, then reports: remotes and who owns them, the branch's state on the
fork and the org, which stage comes next (from the PRs GitHub already has), the commits and files
each stage would carry, a merge simulation against the stage's base, migration numbers against
main and staging (the same rules as .github/ci/check-migration-numbers.sh), risk flags from the
paths touched, CI runs on the org head, and any /feature job folder that belongs to the branch.

Nothing is written, pushed or opened. Exit 0 always; blockers are in the report.
"""
import argparse, glob, json, os, re, subprocess, sys

RISK = [
    ("database migration", r"prisma/migrations/"),
    ("schema", r"schema\.prisma$"),
    ("auth, roles or scope", r"(lib/auth|api/auth|auth\.config|auth-permissions|/scope|permission|require-feature|feature-catalog|features\.ts|middleware|access-helpers|entity-stamp|/entities|people-models)"),
    ("email", r"(lib/email|/templates/.*\.tsx$|mailer|resend)"),
    ("CI or deployment config", r"(^\.github/|vercel\.json|next\.config|env\.ts|\.env)"),
    ("dependencies", r"(package\.json|package-lock\.json)$"),
    ("external integration", r"(fabric|paylocity|pestroutes|fieldroutes|samsara|talkdesk|openrouter|netsuite|vercel/blob|/blob|/cron/)"),
    ("environment variables", r"(env\.ts$|\.env\.example$)"),
]
MIG_DIR = "app/prisma/migrations"


def sh(*args, ok=(0,), text=True):
    r = subprocess.run(list(args), capture_output=True, text=text, encoding="utf-8" if text else None, errors="replace" if text else None)
    return (r.stdout.strip() if r.returncode in ok else None), r.returncode, r.stderr.strip()


def git(*args, ok=(0,)):
    return sh("git", *args, ok=ok)[0]


def gh_json(*args):
    out, code, err = sh("gh", *args)
    if code != 0 or not out:
        return None
    try:
        return json.loads(out)
    except ValueError:
        return None


def remotes():
    out = git("remote", "-v") or ""
    seen = {}
    for line in out.splitlines():
        m = re.match(r"(\S+)\s+(\S+)\s+\((fetch|push)\)", line)
        if not m or m.group(3) != "fetch":
            continue
        name, url = m.group(1), m.group(2)
        slug = re.sub(r"\.git$", "", re.sub(r"^(https://github\.com/|git@github\.com:)", "", url))
        seen[name] = slug
    return seen


def migrations_at(ref):
    out = git("ls-tree", "--full-tree", "--name-only", f"{ref}:{MIG_DIR}")
    return sorted(d for d in (out or "").splitlines() if re.match(r"^\d{4}_", d))


def new_migrations(base, head):
    out = git("diff", "--name-only", "--diff-filter=A", f"{base}...{head}", "--", f":(top){MIG_DIR}") or ""
    dirs = set()
    for p in out.splitlines():
        m = re.search(r"/prisma/migrations/([^/]+)/", p)
        if m and re.match(r"^\d{4}_", m.group(1)):
            dirs.add(m.group(1))
    return sorted(dirs)


def migration_check(base, head):
    """Same rules as the CI script: reuse of a taken number, at/below the base's highest, duplicates."""
    base_list = migrations_at(base)
    if not base_list:
        return {"base": base, "ok": None, "note": f"could not list migrations on {base}"}
    nums = [int(d[:4]) for d in base_list]
    highest = max(nums)
    added = new_migrations(base, head)
    problems = []
    for d in added:
        n = int(d[:4])
        taken = [b for b in base_list if b.startswith(d[:4] + "_")]
        if taken:
            problems.append(f"{d} reuses {d[:4]}, taken on {base} by {', '.join(taken)}")
        elif n <= highest:
            problems.append(f"{d} is at or below the highest on {base} ({highest:04d}); renumber to {highest + 1:04d} or higher")
    counts = {}
    for d in added:
        counts[d[:4]] = counts.get(d[:4], 0) + 1
    for n, c in counts.items():
        if c > 1:
            problems.append(f"number {n} used {c} times in this branch")
    return {"base": base, "highest": highest, "added": added, "ok": not problems, "problems": problems}


def commits(rng):
    out = git("log", "--format=%h %an%x09%s", rng) or ""
    return [{"sha": l.split(" ", 1)[0], "author": l.split(" ", 1)[1].split("\t")[0], "subject": l.split("\t", 1)[1] if "\t" in l else ""} for l in out.splitlines()]


def merge_sim(base, head):
    out, code, err = sh("git", "merge-tree", "--write-tree", "--name-only", base, head, ok=(0, 1))
    if code not in (0, 1):
        return {"ok": None, "note": "git merge-tree unavailable (needs git 2.38+)"}
    lines = (out or "").splitlines()
    return {"ok": code == 0, "conflicts": lines[1:] if code == 1 else []}


def touched(base, head):
    out = git("diff", "--name-only", f"{base}...{head}") or ""
    return out.splitlines()


def risk_flags(files):
    flags = {}
    for label, pat in RISK:
        hits = [f for f in files if re.search(pat, f)]
        if hits:
            flags[label] = hits[:12]
    return flags


def job_for(branch):
    roots = [os.environ.get("WORKSHOP_FEATURES_DIR"), os.path.join(os.path.expanduser("~"), ".claude", "feature-work")]
    for root in [r for r in roots if r]:
        for sp in glob.glob(os.path.join(root, "*", "status.json")):
            try:
                st = json.load(open(sp, encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if branch and branch in (st.get("branch") or ""):
                d = os.path.dirname(sp)
                files = sorted(os.path.relpath(f, d) for f in glob.glob(os.path.join(d, "**", "*.md"), recursive=True) if "/briefs/" not in f.replace(os.sep, "/"))
                return {"slug": os.path.basename(d), "folder": d, "stage": st.get("stage"), "prs": st.get("prs"), "files": files}
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["1", "2", "3", "sync"], help="Force a stage instead of detecting it")
    ap.add_argument("--branch", help="Task branch (default: the current branch)")
    ap.add_argument("--org", help="The organisation repository, owner/repo (default: the remote that isn't the fork)")
    ap.add_argument("--no-fetch", action="store_true", help="Skip git fetch")
    ap.add_argument("--json", action="store_true", help="Print only the JSON report")
    a = ap.parse_args()

    top = git("rev-parse", "--show-toplevel")
    if not top:
        sys.exit("not inside a git repository")
    os.chdir(top)
    R = {"repo": top, "blockers": [], "warnings": []}

    # Remotes: the fork is the one owned by the gh user (or named origin); the org is the other one.
    rem = remotes()
    me = (gh_json("api", "user", "--jq", "{login: .login}") or {}).get("login")
    fork = next((n for n, s in rem.items() if me and s.lower().startswith(me.lower() + "/")), None) or ("origin" if "origin" in rem else None)
    org = None
    if a.org:
        org = next((n for n, s in rem.items() if s.lower() == a.org.lower()), None)
        if not org:
            R["blockers"].append(f"no remote points at {a.org}")
    else:
        others = [n for n in rem if n != fork]
        org = others[0] if len(others) == 1 else None
        if len(others) > 1:
            R["warnings"].append(f"several non-fork remotes ({', '.join(others)}); pass --org")
    R["remotes"] = {"all": rem, "gh_user": me, "fork": fork, "fork_repo": rem.get(fork), "org": org, "org_repo": rem.get(org)}
    if not fork or not org:
        R["blockers"].append("could not tell the fork remote from the org remote; check git remote -v")
    if not a.no_fetch:
        for n in [x for x in (fork, org) if x]:
            if git("fetch", "--prune", n) is None:
                R["warnings"].append(f"git fetch {n} failed (offline?)")

    branch = a.branch or git("rev-parse", "--abbrev-ref", "HEAD")
    R["branch"] = branch
    R["tree_clean"] = (git("status", "--porcelain") or "") == ""
    R["head"] = git("rev-parse", "--short", "HEAD")
    # The worktree that holds the branch, if any (the docs want one worktree per task).
    R["worktree"] = None
    cur = {}
    for line in (git("worktree", "list", "--porcelain") or "").splitlines() + [""]:
        if line.startswith("worktree "):
            cur = {"path": line[9:]}
        elif line.startswith("branch "):
            cur["branch"] = line[7:].replace("refs/heads/", "")
        elif line == "" and cur:
            if cur.get("branch") == branch:
                wt = cur["path"]
                R["worktree"] = {"path": wt, "clean": (git("-C", wt, "status", "--porcelain") or "") == "", "here": os.path.realpath(wt) == os.path.realpath(top)}
            cur = {}
    org_main, org_staging = f"{org}/main", f"{org}/staging"
    R["bases"] = {"main": git("rev-parse", "--short", org_main), "staging": git("rev-parse", "--short", org_staging)}
    R["staging_ahead_of_main"] = int(git("rev-list", "--count", f"{org_main}..{org_staging}") or 0)
    fork_ref, org_ref = f"{fork}/{branch}", f"{org}/{branch}"
    R["refs"] = {
        "local": git("rev-parse", "--short", branch),
        "fork": git("rev-parse", "--short", fork_ref),
        "org": git("rev-parse", "--short", org_ref),
    }
    if R["refs"]["fork"] and R["refs"]["local"]:
        ahead = git("rev-list", "--count", f"{fork_ref}..{branch}")
        behind = git("rev-list", "--count", f"{branch}..{fork_ref}")
        R["refs"]["local_vs_fork"] = f"ahead {ahead}, behind {behind}"
    R["main_gap_to_staging"] = commits(f"{org_staging}..{org_main}")  # main commits staging doesn't have yet

    # PRs GitHub already has for this branch.
    org_repo = rem.get(org) if org else None
    fork_owner = (rem.get(fork) or "/").split("/")[0]
    # gh matches a bare branch name against every head owner; split fork-owned (PR #1) from org-owned (PR #2, hotfix).
    prs = {"pr1": [], "pr2": [], "pr3": []}
    if org_repo and branch not in ("main", "staging"):
        org_owner = org_repo.split("/")[0].lower()
        for p in gh_json("pr", "list", "--repo", org_repo, "--head", branch, "--state", "all", "--limit", "30",
                         "--json", "number,state,baseRefName,url,mergedAt,title,headRepositoryOwner") or []:
            owner = ((p.get("headRepositoryOwner") or {}).get("login") or "").lower()
            (prs["pr2"] if owner == org_owner else prs["pr1"]).append({**p, "head_owner": owner})
    if org_repo:
        prs["pr3"] = gh_json("pr", "list", "--repo", org_repo, "--head", "staging", "--base", "main", "--state", "open",
                             "--json", "number,state,url,title") or []
    R["prs"] = prs
    pr1_merged = any(p["state"] == "MERGED" for p in prs["pr1"])
    for p in prs["pr1"]:
        if p["state"] != "CLOSED" and p["baseRefName"] != branch:
            R["warnings"].append(f"PR #{p['number']} targets org branch {p['baseRefName']}, not the same-named {branch}")
    pr2 = next((p for p in prs["pr2"] if p["baseRefName"] == "staging" and p["state"] != "CLOSED"), None)
    pr2_merged = bool(pr2 and pr2["state"] == "MERGED")
    in_main = branch not in ("main", "staging") and git("merge-base", "--is-ancestor", branch, org_main) is not None
    in_staging = branch not in ("main", "staging") and git("merge-base", "--is-ancestor", branch, org_staging) is not None

    stage = a.stage
    if not stage:
        if branch in ("staging", "main"):
            stage = "3"
        elif in_main:
            stage = "done"
        elif pr2 and pr2["state"] == "OPEN":
            stage = "2"
        elif pr2_merged or in_staging:
            stage = "3"
        elif pr1_merged:
            stage = "2"
        else:
            stage = "1"
    R["stage"] = stage
    if stage == "done":
        R["note"] = f"{branch} is already contained in {org_main}: nothing to ship"
        print(json.dumps(R, indent=2) if a.json else
              f"Repository: {top}\nBranch: {branch}\n{R['note']}.\n" + ("PRs: " + "; ".join(f"#{p['number']} {p['state']} -> {p['baseRefName']}" for p in prs['pr1'] + prs['pr2']) if prs['pr1'] or prs['pr2'] else ""))
        return

    if stage == "2" and pr2 and pr2["state"] == "OPEN":
        v = gh_json("pr", "view", str(pr2["number"]), "--repo", org_repo, "--json", "mergeable,mergeStateStatus,isDraft,reviewDecision,reviewRequests,latestReviews,updatedAt")
        R["pr2_open"] = {**pr2, **(v or {})}
        if v:
            R["pr2_open"]["requested"] = [(r.get("login") or r.get("name") or "?") for r in (v.get("reviewRequests") or [])]
            R["pr2_open"]["reviews"] = [f"{(r.get('author') or {}).get('login', '?')}: {r.get('state')} {(r.get('submittedAt') or '')[:10]}" for r in (v.get("latestReviews") or [])]
        if v and v.get("mergeable") == "CONFLICTING":
            R["warnings"].append(f"PR #{pr2['number']} conflicts with staging: the sync route (staging-conflicts.md)")
        R["warnings"].append(f"PR #{pr2['number']} is already open: don't open another; a further commit goes fork -> org branch through a follow-up PR #1, and PR #2 picks it up (new commits need a fresh review)")

    if stage == "1":
        base, head = org_main, branch
        if not R["refs"]["org"]:
            R["warnings"].append(f"no org branch {branch} yet: it must be created from {org_main} @ {R['bases']['main']} before PR #1 (create it with the create-only gh api call in SKILL.md)")
        if pr1_merged:
            R["warnings"].append("a PR #1 for this branch is already merged; a new PR #1 would carry only new commits")
        R["commits"] = commits(f"{base}..{head}")
        behind_main = git("rev-list", "--count", f"{head}..{org_main}")
        R["behind_main"] = int(behind_main or 0)
        if R["behind_main"]:
            R["warnings"].append(f"branch is {behind_main} commits behind {org_main}: bring it in before pushing (merge, not rebase, once shared)")
    elif stage == "2":
        base, head = org_staging, (org_ref if R["refs"]["org"] else branch)
        if not pr1_merged:
            R["blockers"].append("PR #1 is not merged on GitHub; PR #2 opens only after it has actually merged")
        if R["refs"]["org"] and R["refs"]["fork"] and git("merge-base", "--is-ancestor", fork_ref, org_ref) is None:
            R["warnings"].append(f"the org branch does not contain the fork branch's head ({R['refs']['fork']}); PR #1 may not include your latest commits")
        R["commits"] = commits(f"{base}..{head}")
        own = commits(f"{org_main}..{head}")
        own_shas = {c["sha"] for c in own}
        foreign = [c for c in R["commits"] if c["sha"] not in own_shas]
        R["foreign_commits"] = foreign
        if foreign:
            R["blockers"].append(f"{len(foreign)} commits in {base}..{head} are not this task's (main is ahead of staging): get the main -> staging sync merged first, or rebuild on staging")
    elif stage == "3":
        base, head = org_main, org_staging
        R["commits"] = commits(f"{base}..{head}")
        merged = gh_json("pr", "list", "--repo", org_repo, "--base", "staging", "--state", "merged", "--limit", "60",
                         "--json", "number,title,url,mergedAt,mergeCommit,headRefName,author") or [] if org_repo else []
        full = {c[:7]: c for c in ((git("log", "--format=%H", f"{base}..{head}") or "").splitlines())}
        R["included_prs"] = [{"number": p["number"], "title": p["title"], "url": p["url"], "head": p.get("headRefName"),
                              "author": (p.get("author") or {}).get("login"), "merged": (p.get("mergedAt") or "")[:10],
                              "sync": p.get("headRefName") == "main"}
                             for p in merged if (p.get("mergeCommit") or {}).get("oid", "")[:7] in full]
        if prs["pr3"]:
            R["warnings"].append(f"a release PR is already open: {prs['pr3'][0]['url']}")
    else:  # sync
        base, head = org_staging, (org_ref if R["refs"]["org"] else branch)
        R["commits"] = commits(f"{base}..{head}")

    R["range"] = f"{base}..{head}"
    R["files"] = touched(base, head)
    R["diff_stat"] = (git("diff", "--shortstat", f"{base}...{head}") or "").strip()
    R["merge"] = merge_sim(base, head)
    if R["merge"].get("ok") is False:
        R["warnings"].append(f"merging {head} into {base} conflicts in: {', '.join(R['merge']['conflicts'][:8])}")
        for f in R["merge"]["conflicts"][:8]:
            who = git("log", "--format=%h %s", "-3", f"{git('merge-base', base, head)}..{base}", "--", f) or ""
            R.setdefault("conflict_sources", {})[f] = who.splitlines()
    R["risk"] = risk_flags(R["files"])
    R["migrations"] = {"vs_main": migration_check(org_main, head), "vs_staging": migration_check(org_staging, head)}
    highs = [mc["highest"] for mc in R["migrations"].values() if mc.get("highest")]
    if highs and any(mc.get("problems") for mc in R["migrations"].values()):
        target = max(highs) + 1
        R["migration_target"] = target
        R["blockers"].append(f"migration numbers: renumber this branch's migrations to {target:04d} and up (above both main {highs[0]:04d} and staging {highs[-1]:04d}); "
                             f"`cd app && npx tsx scripts/renumber-migrations.ts --base {org_staging}` previews it, `--apply` does it (a migration edit: needs the human's yes), then `--check`")
    else:
        for k, mc in R["migrations"].items():
            for p in mc.get("problems", []):
                R["blockers"].append(f"migration {k.replace('vs_', 'against ')}: {p}")
    if org_repo and stage in ("2", "3", "sync"):
        runs = gh_json("run", "list", "--repo", org_repo, "--branch", "staging" if stage == "3" else branch, "--limit", "4",
                       "--json", "name,status,conclusion,headSha,url,createdAt") or []
        base_date = git("log", "-1", "--format=%cI", base) or ""
        R["ci"] = [{"name": r["name"], "status": r["status"], "conclusion": r.get("conclusion"), "sha": r["headSha"][:7], "url": r["url"],
                    "date": (r.get("createdAt") or "")[:10], "before_base_moved": (r.get("createdAt") or "") < base_date} for r in runs]
        if any(c["before_base_moved"] for c in R["ci"]):
            R["warnings"].append(f"the CI runs on {branch} predate the last change to {base} ({base_date[:10]}): a green run from before the base moved is not proof; the PR's checks re-run on the next push")
    R["job"] = job_for(branch)
    if R["job"] and R["job"].get("prs"):
        gh_states = {1: "merged" if pr1_merged else ("open" if any(p["state"] == "OPEN" for p in prs["pr1"]) else "not_started"),
                     2: pr2["state"].lower() if pr2 else "not_started"}
        for p in R["job"]["prs"]:
            n = p.get("number")
            if n in gh_states and (p.get("state") or "not_started") != gh_states[n]:
                R["warnings"].append(f"the job's status.json says PR #{n} is {p.get('state')}, GitHub says {gh_states[n]}: the folder is stale; GitHub is the truth, update the folder only to what GitHub shows")
    if not R["tree_clean"]:
        R["warnings"].append("working tree has uncommitted changes")

    if a.json:
        print(json.dumps(R, indent=2))
        return

    P = print
    P(f"Repository: {top}")
    P(f"Remotes: fork = {fork} ({rem.get(fork)}), org = {org} ({rem.get(org)}), gh user = {me}")
    P(f"Branch: {branch}  local {R['refs']['local'] or 'absent'} · fork {R['refs']['fork'] or 'not pushed'} · org {R['refs']['org'] or 'absent'}"
      + (f" · local vs fork: {R['refs']['local_vs_fork']}" if R["refs"].get("local_vs_fork") else "")
      + (f"  (checkout is on {git('rev-parse', '--abbrev-ref', 'HEAD')} @ {R['head']})" if a.branch and a.branch != git("rev-parse", "--abbrev-ref", "HEAD") else ""))
    P(f"Bases: {org_main} @ {R['bases']['main']} · {org_staging} @ {R['bases']['staging']} · staging ahead of main by {R['staging_ahead_of_main']} commits · main ahead of staging by {len(R['main_gap_to_staging'])}")
    wt = R.get("worktree")
    if wt and wt["here"]:
        P(f"Worktree: this checkout holds {branch} · working tree {'clean' if wt['clean'] else 'DIRTY'}")
    elif wt:
        P(f"Worktree for {branch}: {wt['path']} (working tree {'clean' if wt['clean'] else 'DIRTY'}) · this checkout: {'clean' if R['tree_clean'] else 'DIRTY'}")
    else:
        P(f"Worktree for {branch}: none (add one before working on it: git worktree add ../<name> {branch}) · this checkout: {'clean' if R['tree_clean'] else 'DIRTY'}")
    P(f"\nStage: {'#' + stage if stage != 'sync' else 'sync (resolve conflicts with staging)'}")
    for k, label in (("pr1", "PR #1"), ("pr2", "PR #2"), ("pr3", "PR #3")):
        for p in prs[k]:
            P(f"  {label}: #{p['number']} {p['state']} -> {p.get('baseRefName', 'main')} {p['url']}")
    if R.get("pr2_open"):
        o = R["pr2_open"]
        P(f"  PR #2 state: mergeable={o.get('mergeable')} {o.get('mergeStateStatus')} draft={o.get('isDraft')} review={o.get('reviewDecision')} updated {(o.get('updatedAt') or '')[:10]}")
        P(f"  reviewers requested: {', '.join(o.get('requested') or []) or 'none'} · reviews: {'; '.join(o.get('reviews') or []) or 'none'}")
    if R.get("included_prs") is not None:
        P(f"\nPRs merged into staging since main ({len(R['included_prs'])}):")
        for p in R["included_prs"]:
            P(f"  #{p['number']} {p['title']} ({'main -> staging sync' if p['sync'] else p['head']}, {p['author']}, {p['merged']}) {p['url']}")
    plain = [c for c in R["commits"] if not c["subject"].startswith("Merge ")]
    P(f"\nRange {R['range']}: {len(R['commits'])} commits ({len(plain)} without merges) · {R['diff_stat'] or 'no diff'}")
    for c in plain[:25]:
        P(f"  {c['sha']} {c['subject']}  ({c['author']})")
    if len(plain) > 25:
        P(f"  … {len(plain) - 25} more")
    if R.get("foreign_commits"):
        P(f"  NOT this task's ({len(R['foreign_commits'])}): " + ", ".join(c["sha"] for c in R["foreign_commits"][:10]))
    P(f"\nFiles ({len(R['files'])}):")
    for f in R["files"][:40]:
        P(f"  {f}")
    if len(R["files"]) > 40:
        P(f"  … {len(R['files']) - 40} more")
    if R["risk"]:
        P("\nRisk flags:")
        for k, v in R["risk"].items():
            P(f"  {k}: " + ", ".join(v[:6]) + (" …" if len(v) > 6 else ""))
    m = R["merge"]
    P(f"\nMerge simulation {head} -> {base}: " + ("clean" if m.get("ok") else ("CONFLICTS: " + ", ".join(m["conflicts"]) if m.get("ok") is False else m.get("note", "?"))))
    for f, who in (R.get("conflict_sources") or {}).items():
        P(f"  {f} changed on {base} by: " + "; ".join(who))
    for k, mc in R["migrations"].items():
        label = k.replace("vs_", "against ")
        if mc.get("ok") is None:
            P(f"Migrations {label}: {mc.get('note')}")
        else:
            P(f"Migrations {label}: highest {mc['highest']:04d}; added {', '.join(mc['added']) or 'none'}; " + ("OK" if mc["ok"] else "PROBLEM: " + "; ".join(mc["problems"])))
    if R.get("migration_target"):
        P(f"Migration target: {R['migration_target']:04d} (above both bases)")
    if R.get("ci"):
        P("\nCI on the org head:")
        for r in R["ci"]:
            P(f"  {r['name']}: {r['status']} {r.get('conclusion') or ''} @ {r['sha']} on {r['date']}{' (before the base last moved)' if r['before_base_moved'] else ''} {r['url']}")
    if R["job"]:
        j = R["job"]
        P(f"\n/feature job: {j['slug']} (stage {j['stage']}) at {j['folder']}")
        P("  files: " + ", ".join(j["files"]))
    if R["blockers"]:
        P("\nBLOCKERS:")
        for b in R["blockers"]:
            P(f"  - {b}")
    if R["warnings"]:
        P("\nWarnings:")
        for w in R["warnings"]:
            P(f"  - {w}")
    if not R["blockers"] and not R["warnings"]:
        P("\nNo blockers, no warnings.")


if __name__ == "__main__":
    main()
