# AGENTS.md

## Project guidance

Use the `big-project-orchestrator` skill for any medium or large task that should be planned, implemented, validated, and archived in milestones.

## Durable project memory

The canonical project-memory files live in `.codex/orchestrator/`:

- `new_requirements.md`
- `current_requirements.md`
- `todo.md`
- `decisions.md`
- `status.md`
- `handoff.md`
- `planner_history.txt`

Before any large implementation, refine the active milestone and make sure acceptance criteria plus validation commands are written down.

## Working rules

- Prefer small, reviewable diffs.
- Run validation before handoff.
- Update `status.md` and `handoff.md` before stopping.
- Record non-obvious tradeoffs in `decisions.md`.
- Archive completed milestones instead of letting files drift indefinitely.

## Worktree guidance

For risky or parallel work, prefer Codex app Worktree mode or separate branches. Keep each thread focused on one checklist slice from `todo.md`.
