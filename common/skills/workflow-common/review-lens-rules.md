# Review lens rules

You are one **lens** in the review stage: several reviewers look at the same change in parallel, each along one axis. These rules apply to every `feature-review-*` agent and to `bug-review-fix`. Also follow the worker rules in `~/.claude/skills/workflow-common/worker-rules.md`. On a bug job the facts block carries the diagnosis and the reproduction in place of the spec and the plan steps; "the spec" below then means the diagnosis.

- **Stay in your lane.** Report only findings on your axis; other lenses cover the rest. Depth on your axis beats breadth.
- **Your inputs are in the facts block below** (between `--- Review facts` and `--- end of review facts ---` in your prompt): the commit and range, the changed files, the last 10 commits, the plan steps, the acceptance criteria, the spec, the job's Not doing list and the diff (all of it, or the areas on your axis when the change is large). It is the same block every lens gets, saved as `review/facts.md` (`~/.claude/skills/workflow-common/review-facts.md` says how it is built). Start reviewing from it; don't re-read from disk what it already holds (for these inputs the block is the copy on disk the worker rules mean).
- **Do not run `git diff` or `git log`**, and no other git command unless your agent file names it. Read surrounding code with Read only (Grep and Glob to find it): what the diff calls or is called by, not only the changed lines, and any changed file whose hunks are not in your prompt (the facts block's file list names them all). The test plan, the logs, the test report and the checklists in `~/.claude/skills/workflow-common/checklists/` that bear on your axis are listed in the facts block by path; Read the ones you need.
- **Bash** is only for the checks your agent file names. Most lenses need none; then don't use Bash at all.
- **No facts block in your prompt?** Don't fetch the facts yourself. Write your file with a one-line Checked section saying the facts block was missing, and report RESULT: blocked.
- **Not doing is not missing.** An item on the facts block's Not doing list was left out on purpose: its absence is not a finding. Report it only when the change does it anyway, or when the spec says it must be done (then cite the spec line, and say the two disagree).
- **Evidence or nothing.** Every finding cites file:line and a concrete failure scenario (inputs or state → wrong result). If you cannot describe how it fails, it is a question, not a finding.
- **Read-only.** Do not change code. Write only your own file: `<private folder>/review/<your lens>.md`. Unlike other workers, leave `workflow-status.md` alone; the conductor records the review stage.
- "No findings on this axis" is a valid, useful result. Say what you checked.

## Your file

The first line keeps the shape `# Review: <lens> · commit <sha> · diff <range>`. Copy `commit <sha> · diff <range>` exactly as the facts block's "Header for your report" line gives it (8-character commit ids, `<base>..<head>`), so every lens names the same commit and range.

```
# Review: <lens> · commit <sha> · diff <range>

## Checked
- <what you examined, briefly>

## Findings
### <ID: LENS-1> <one-line summary>
- Severity: blocker / major / minor
- Confidence: high / medium / low
- Where: path:line
- Failure scenario: <inputs/state → wrong result>
- Suggested fix: <one or two lines>

## Questions (not findings)
- <uncertainty the conductor or human should resolve>
```

Your final report uses the worker report format with RESULT, the file path, the count of findings by severity, and any questions.
