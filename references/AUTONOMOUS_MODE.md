# Autonomous Mode

`Phase 2A` adds an autonomous single-thread runner for large project execution.

## Goal

After one explicit user request, Codex should be able to:

- initialize orchestrator state
- derive milestones from a large spec
- activate the current milestone
- run verification
- run mandatory review/hardening
- attempt safe local repairs
- archive completed milestones
- continue until the project is complete or a real blocker is hit

## Entry point

```bash
python3 <skill-dir>/scripts/run_autonomous_cycle.py --repo "$PWD" --resume
```

For greenfield repos with only `spec.md` or `requirements.md`:

```bash
python3 <skill-dir>/scripts/run_autonomous_cycle.py --repo "$PWD" --allow-structure-generation --resume
```

To pair autonomous mode with worktree planning:

```bash
python3 <skill-dir>/scripts/run_autonomous_cycle.py --repo "$PWD" --plan-tracks --resume
```

To also emit runnable track dispatch/bootstrap artifacts:

```bash
python3 <skill-dir>/scripts/run_autonomous_cycle.py --repo "$PWD" --plan-tracks --generate-dispatch --resume
```

## State model

Autonomous mode persists machine-readable state in:

- `.codex/orchestrator/state.json`
- `.codex/orchestrator/last_verification.json`

Human-readable state still lives in:

- `current_requirements.md`
- `todo.md`
- `status.md`
- `handoff.md`
- `review.md`
- `decisions.md`
- `planner_history.txt`

## Stop conditions

Autonomous mode should continue unless one of these is true:

- the project is complete
- a required secret, credential, or external dependency is missing
- the spec is internally contradictory in a way that blocks safe implementation
- safe repair attempts are exhausted
- the local environment cannot execute the next verification or bootstrap step

## Repair policy

The repair loop is intentionally conservative in `Phase 2A`.

It may:

- generate a concrete `verification.commands.sh`
- generate `review.md` findings
- synchronize validation commands into `current_requirements.md`
- create missing greenfield bootstrap files

It must not:

- invent external services
- add network dependencies without an explicit user request
- silently skip failing verification

## Resume policy

If `state.json` exists, reruns should continue from the recorded phase and active
milestone instead of rebuilding the workspace from scratch.

## Boundaries

`Phase 2A` is the autonomous state machine and local bootstrap layer. It is not
yet a full persistent multi-agent runtime. In Codex app, the code-writing engine
is still Codex itself; the runner keeps the plan, verification surface, and
durable artifacts coherent across long-horizon work.
