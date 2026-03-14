# Multi-Track and Worktree Execution

## When to use

Use this workflow when one milestone is too large for a single narrow diff and should be split into parallel reviewable tracks.

## What it is

The skill can plan multiple lanes, generate track prompts, and emit worktree dispatch artifacts so each track can be handled in isolation before convergence and merge hardening.

## Prompt

```text
$big-project-orchestrator

This milestone is too large for a single implementation lane.
Split it into reviewable tracks and prepare worktree-friendly execution.

Use track planning and dispatch artifacts.
Keep the milestone goal fixed, create only the minimum tracks needed, and prepare the repo for convergence after the tracks are complete.
Do not expand the milestone scope while splitting the work.
```

## Expected outputs

- `tracks.json`
- `track_board.md`
- per-track briefs in `.codex/orchestrator/tracks/`
- optional dispatch artifacts for worktrees
- later convergence and merge orchestration artifacts

## Notes

- this is an advanced workflow because it adds coordination overhead
- use it only when one milestone is genuinely too large for a single lane
