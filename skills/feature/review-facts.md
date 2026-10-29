# Review facts

The **facts block** is everything the review lenses need to know about the change, gathered once by the conductor and pasted into every lens prompt. Lenses then start reviewing on their first turn instead of each fetching the diff, the spec and the plan themselves, and they all see the same commit and the same range.

## When and where

- Build it once per review round, just before dispatching the lenses, and save it as `review/facts.md` in the job's private folder. A re-review round after fixes gets its own file for the new head: `review/facts-r<round>.md` (`facts-r2.md`, …). Never edit a facts file once lenses have been sent it.
- Build it with read-only git in the task's worktree (`git -C <worktree> …`) and the Read tool, and write it with the Write tool.
- Paste it into every lens dispatch between the two marker lines below. The prompt says where it came from, so a lens never has to look for it.

```
--- Review facts (<private folder>/review/facts.md, round <n>) ---
<the file's contents, or for a large diff the shared sections plus this lens's diff sections>
--- end of review facts ---
```

## What goes in it, in this order

1. **Commit and range.** The head commit of the feature branch (`git -C <worktree> rev-parse HEAD`), the base commit (recorded in `workflow-status.md` when the worktree was made), the branch and the worktree path. Then the short forms every lens copies into its report header: `commit <first 8 of head> · diff <first 8 of base>..<first 8 of head>`.
2. **Changed files.** The output of `git -C <worktree> diff --stat <base>..<head>`, as it is.
3. **Recent commits.** `git -C <worktree> log -10 --format='%h %s' <head>`: the last 10 commit subjects, newest first. Those after the base are this change; say how many that is.
4. **Plan steps.** The implementation plan's step list, one line per step (its heading), with the plan's version. On the quick flow, the quick plan's "Where" list.
5. **Acceptance criteria.** `acceptance.md` as it is, with its version. When the job has none, the spec's acceptance criteria (or the quick plan's numbered criteria), and say which.
6. **Spec.** The spec in full, with its path and version. When the job's options use a stand-in (`quick-plan.md`, `requirements.md` or a provided document), paste that instead and name it; when the spec stage was skipped, say so in one line.
7. **Not doing.** The job's `## Not doing` list from `decisions.md` in the private folder, its lines as they are (`- <item> (<reason>)`), under the heading `## Not doing`. When the file has no such list or it is empty, the one line "none". These are things the job left out on purpose; the lens rules say how lenses treat them.
8. **Other inputs, by path only.** The test plan, `dev-tests.md`, `implementation-log.md`, `test-report.md`, `findings.md`, `wireframes.json` and the checklists for this job's layer tags (`~/.claude/skills/feature/checklists/`), each with its version, or "none" when the job has no such file. Lenses read these with the Read tool when their axis needs them; they are not pasted.
9. **The diff.** See below.

## The diff

Count the changed lines with `git -C <worktree> diff --shortstat <base>..<head>` (insertions plus deletions). Lockfiles (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`) are never pasted; they show in the stat. Leave them out of every diff command with `':(exclude,glob)**/package-lock.json' ':(exclude,glob)**/yarn.lock' ':(exclude,glob)**/pnpm-lock.yaml'`.

**Under 1,500 lines:** paste the whole diff, `git -C <worktree> diff <base>..<head> -- . <lockfile excludes>`, under one heading, `### Diff (all files)`. Every lens gets all of it.

**1,500 lines or more:** split the diff into four areas, each under its own heading, and give each lens only the areas on its axis. The stat (section 2) still lists every file, so a lens can open any other changed file with Read.

`server` takes whatever the other three leave, so every changed file except a lockfile is in some area.

| Area | Files | Pathspec after `--` |
|---|---|---|
| `db` | migrations, SQL, Prisma schema | `':(glob)**/migrations/**' ':(glob)**/*.sql' ':(glob)**/*.prisma'` |
| `tests` | test files | `':(glob)**/*.test.*' ':(glob)**/*.spec.*' ':(glob)**/__tests__/**' ':(glob)**/e2e/**'` |
| `ui` | components, pages and styles that are not tests | `':(glob)**/*.tsx' ':(glob)**/*.jsx' ':(glob)**/*.css' ':(glob)**/*.scss' ':(exclude,glob)**/*.test.*' ':(exclude,glob)**/*.spec.*' ':(exclude,glob)**/__tests__/**'` |
| `server` | everything else | `. ':(exclude,glob)**/migrations/**' ':(exclude,glob)**/*.sql' ':(exclude,glob)**/*.prisma' ':(exclude,glob)**/*.test.*' ':(exclude,glob)**/*.spec.*' ':(exclude,glob)**/__tests__/**' ':(exclude,glob)**/e2e/**' ':(exclude,glob)**/*.tsx' ':(exclude,glob)**/*.jsx' ':(exclude,glob)**/*.css' ':(exclude,glob)**/*.scss'` plus the lockfile excludes |

Headings are `### Diff · db`, `### Diff · tests`, `### Diff · ui`, `### Diff · server`; an area with no changed files is one line, "No changes in this area." Each lens gets these areas:

| Lens | Areas |
|---|---|
| `spec` (`feature-reviewer`) | server, db, ui |
| `permissions` | server, db, ui |
| `tests` | tests, server |
| `conventions` | server, db, ui |
| `errors` | server, ui |
| `db` | db, server |
| `performance` | server, ui |
| `ui` | ui |

The facts file holds every area once; each lens prompt carries sections 1 to 8 plus its own areas, and its first line after the marker says which areas it got: "Diff areas in this prompt: server, ui (the diff was 2,589 lines)." When a lens's areas still come to more than 1,500 lines, paste them all the same and note in the review brief that the change is large enough to be worth splitting next time.

## Example (top of a facts file)

```
# Review facts · orbit-465-freeze · round 1

## Commit and range
- Head: edaf0a01c3… on feature/talent-ratings-freeze, worktree /Users/me/Projects/orbit-talent-ratings-freeze
- Base: 556a8214d9… (moxie/main when the worktree was made)
- Header for your report: commit edaf0a01 · diff 556a8214..edaf0a01

## Changed files
 app/prisma/schema.prisma | 41 ++
 …
 20 files changed, 2552 insertions(+), 37 deletions(-)

## Recent commits (7 after the base)
edaf0a01 feat(talent): add the freeze ratings control for admins
…
```
