# Workflow

This document explains how to run the skill effectively in the Codex app and Codex CLI.

## Recommended operating pattern

### 1) Freeze the target
Put the raw request or refined scope into `.codex/orchestrator/new_requirements.md`.

### 2) Promote one milestone
Turn that into one active, testable milestone:

```bash
python3 <skill-dir>/scripts/promote_requirements.py --repo "$PWD" --title "milestone-short-name"
```

### 3) Implement only the active milestone
Avoid coding against a fuzzy or sprawling brief. Keep the active scope in `current_requirements.md`.

### 4) Validate before moving on
Run either the repo-specific verifier:

```bash
bash .codex/orchestrator/verification.commands.sh
```

or the bundled verifier:

```bash
bash <skill-dir>/scripts/verify_repo.sh "$PWD"
```

### 5) Review before archive
Run a mandatory review pass after verification succeeds:

```bash
python3 <skill-dir>/scripts/run_review_pass.py --repo "$PWD"
```

### 6) Update durable memory
Refresh `status.md`, `handoff.md`, `todo.md`, and `decisions.md`.

### 7) Archive
Archive the finished cycle so the next one starts clean:

```bash
python3 <skill-dir>/scripts/archive_cycle.py --repo "$PWD" --label "milestone-short-name"
```

## Autonomous mode

For large specs where Codex should keep moving milestone-by-milestone, prefer:

```bash
python3 <skill-dir>/scripts/run_autonomous_cycle.py --repo "$PWD" --resume
```

Greenfield repos can allow local structure generation:

```bash
python3 <skill-dir>/scripts/run_autonomous_cycle.py --repo "$PWD" --allow-structure-generation --resume
```

If the active milestone is large enough for parallel lanes, generate a track
plan as part of the cycle:

```bash
python3 <skill-dir>/scripts/run_autonomous_cycle.py --repo "$PWD" --plan-tracks --resume
```

This mode bootstraps `state.json`, plans milestones, runs verification, runs a
mandatory review gate, attempts safe local repairs, and archives finished
milestones. It should only stop on a real blocker or at project completion.

## Codex app mode

Use the Codex app when you want:

- visual diff review
- multiple parallel worktree threads
- recurring local automations
- quick manual steering while keeping everything local

### Good thread split

- Main thread: active implementation
- Worktree thread 1: tests / coverage
- Worktree thread 2: reviewer / hardening
- Worktree thread 3: docs / migration notes

For a durable split, generate track artifacts first:

```bash
python3 <skill-dir>/scripts/plan_tracks.py --repo "$PWD"
```

If you also want ready-to-run worktree bootstrap commands:

```bash
python3 <skill-dir>/scripts/generate_track_dispatch.py --repo "$PWD"
```

If you want ready-to-paste prompts for each lane:

```bash
python3 <skill-dir>/scripts/generate_track_prompts.py --repo "$PWD"
```

Before converging parallel lanes back into one milestone, evaluate readiness:

```bash
python3 <skill-dir>/scripts/evaluate_track_readiness.py --repo "$PWD"
```

Then prepare the convergence brief:

```bash
python3 <skill-dir>/scripts/prepare_track_convergence.py --repo "$PWD"
```

Then run the post-convergence merge cycle:

```bash
python3 <skill-dir>/scripts/orchestrate_track_merge.py --repo "$PWD"
```

At any point during multi-track execution, refresh the supervisor report:

```bash
python3 <skill-dir>/scripts/run_track_supervisor.py --repo "$PWD"
```

Then materialize the next executable handoff:

```bash
python3 <skill-dir>/scripts/generate_execution_bridge.py --repo "$PWD"
```

If the next step is in the safe auto-orchestration set, run it directly:

```bash
python3 <skill-dir>/scripts/orchestrate_next_action.py --repo "$PWD"
```

Before a real project kickoff, validate the orchestration graph:

```bash
python3 <skill-dir>/scripts/validate_orchestrator_state.py --repo "$PWD"
```

If the fleet is blocked or the merge cycle fails, refresh the escalation playbook:

```bash
python3 <skill-dir>/scripts/generate_escalation_playbook.py --repo "$PWD"
```

For recurring report-only automation runs, refresh the full supervisory stack:

```bash
python3 <skill-dir>/scripts/run_automation_cycle.py --repo "$PWD"
```

If the report looks stable, generate the reusable automation profile pack:

```bash
python3 <skill-dir>/scripts/generate_automation_pack.py --repo "$PWD"
```

## Codex CLI mode

Use Codex CLI when you want:

- interactive terminal-native work
- `codex exec` scripting
- experimental multi-agent roles
- batch fan-out reviews with `spawn_agents_on_csv`

### Suggested CLI prompt

```text
$big-project-orchestrator

Read the current milestone and run this as a disciplined loop:
plan -> implement -> validate -> repair -> update status -> stop.
Do not start milestone 2 before milestone 1 is archived.
```

## Durable memory philosophy

The durable files are not a formality. They are the mechanism that keeps long-horizon tasks coherent across:

- pauses
- worktree switches
- handoffs
- verification failures
- report-only automation runs

## Report-first jobs

A report-first job is a task that should inspect and summarize before editing, for example:

- nightly verification
- release-readiness audit
- docs drift
- coverage gaps
- branch risk review

For report-first jobs, say so explicitly and tell Codex **not** to edit code.

If the workflow is already stable, prefer `run_automation_cycle.py` as the recurring automation entrypoint because it refreshes the supervisory artifacts without enabling repair or implementation edits.

`Phase 5B` adds `generate_automation_pack.py`, which turns the current supervisory state into reusable recurring prompt/contracts and schedule hints for Codex app automations.

`Phase 5C` adds `update_automation_memory.py`, which keeps a durable memory of open, new, recurring, and resolved findings so automation reports do not treat the same issue as new forever.

`Phase 6A` adds `generate_execution_bridge.py`, which converts the fleet-level recommendation into an execution-ready handoff with concrete commands, inputs, and expected outputs.

`Phase 6B` adds `orchestrate_next_action.py`, which executes the next safe orchestration step and records whether the system proceeded automatically or stopped for human intervention.

`Phase 7A` adds shared action contracts and `validate_orchestrator_state.py`, tightening manifest/state invariants so stale supervisor, bridge, or orchestration state is caught early.
