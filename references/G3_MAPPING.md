# Mapping from g3 ideas to Codex-native equivalents

This skill is designed to preserve the spirit of g3 while using Codex-native primitives.

## g3 planning mode
g3 keeps requirements, todos, and planner history in `g3-plan/`.

**This skill instead uses** `.codex/orchestrator/` with:
- `new_requirements.md`
- `current_requirements.md`
- `todo.md`
- `planner_history.txt`
- `completed/`

## g3 coach/player loop
g3 uses separate implementation and review roles.

**This skill uses**
- Codex app: separate worktree threads
- Codex CLI: optional `explorer`, `reviewer`, `worker`, and `monitor` roles

## g3 studio
g3 studio isolates agents in worktrees.

**This skill uses**
- Codex app built-in Worktree threads
- Codex app automations for recurring background work
- durable track manifests in `.codex/orchestrator/tracks.json` and `track_board.md`

## g3 context management
g3 has explicit thinning and compaction tools.

**This skill uses**
- durable project memory in markdown
- milestone-sized scopes
- explicit handoffs
- reviewable diffs
- status rendering and archival

## g3 TODO tooling
g3 has session TODO tools.

**This skill uses**
- repo-visible `todo.md`
- archived milestone state
- explicit history log
