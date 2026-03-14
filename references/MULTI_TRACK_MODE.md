# Multi-Track Mode

`Phase 2C` adds durable planning for worktree-style parallel execution.

## Goal

Split one active milestone into a small set of focused tracks so Codex app
worktrees or Codex CLI roles can work in parallel without drifting from the
same milestone contract.

## Entry points

Create a track plan for the active milestone:

```bash
python3 <skill-dir>/scripts/plan_tracks.py --repo "$PWD"
```

Run the autonomous cycle and create tracks at the same time:

```bash
python3 <skill-dir>/scripts/run_autonomous_cycle.py --repo "$PWD" --plan-tracks --resume
```

Update one track:

```bash
python3 <skill-dir>/scripts/update_track_status.py --repo "$PWD" --track track-01-implementation-lane --status in_progress
```

Generate runnable dispatch/bootstrap artifacts:

```bash
python3 <skill-dir>/scripts/generate_track_dispatch.py --repo "$PWD"
```

Generate role-aware prompt packs:

```bash
python3 <skill-dir>/scripts/generate_track_prompts.py --repo "$PWD"
```

Evaluate whether tracks are ready to merge back:

```bash
python3 <skill-dir>/scripts/evaluate_track_readiness.py --repo "$PWD"
```

Prepare the milestone-level convergence brief:

```bash
python3 <skill-dir>/scripts/prepare_track_convergence.py --repo "$PWD"
```

Run post-convergence verify/review/hardening:

```bash
python3 <skill-dir>/scripts/orchestrate_track_merge.py --repo "$PWD"
```

Run the fleet supervisor to recommend the next lane-level action:

```bash
python3 <skill-dir>/scripts/run_track_supervisor.py --repo "$PWD"
```

Generate the concrete next-step handoff from that recommendation:

```bash
python3 <skill-dir>/scripts/generate_execution_bridge.py --repo "$PWD"
```

Execute the next safe orchestration step:

```bash
python3 <skill-dir>/scripts/orchestrate_next_action.py --repo "$PWD"
```

Validate state alignment across supervisor, bridge, and orchestration:

```bash
python3 <skill-dir>/scripts/validate_orchestrator_state.py --repo "$PWD"
```

Generate the escalation/recovery playbook:

```bash
python3 <skill-dir>/scripts/generate_escalation_playbook.py --repo "$PWD"
```

Run the report-first automation supervisory cycle:

```bash
python3 <skill-dir>/scripts/run_automation_cycle.py --repo "$PWD"
```

Generate reusable recurring automation profiles from the current state:

```bash
python3 <skill-dir>/scripts/generate_automation_pack.py --repo "$PWD"
```

## Durable artifacts

Multi-track mode writes:

- `.codex/orchestrator/tracks.json`
- `.codex/orchestrator/track_board.md`
- `.codex/orchestrator/tracks/*.md`
- `.codex/orchestrator/dispatch.json`
- `.codex/orchestrator/dispatch/*.sh`
- `.codex/orchestrator/dispatch/*.md`
- `.codex/orchestrator/prompts.json`
- `.codex/orchestrator/prompts/*.md`
- `.codex/orchestrator/track_readiness.json`
- `.codex/orchestrator/track_readiness.md`
- `.codex/orchestrator/convergence.json`
- `.codex/orchestrator/convergence.md`
- `.codex/orchestrator/merge_report.json`
- `.codex/orchestrator/merge_report.md`
- `.codex/orchestrator/supervisor_report.json`
- `.codex/orchestrator/supervisor_report.md`
- `.codex/orchestrator/escalation_report.json`
- `.codex/orchestrator/escalation_report.md`
- `.codex/orchestrator/automation_report.json`
- `.codex/orchestrator/automation_report.md`
- `.codex/orchestrator/automation_pack.json`
- `.codex/orchestrator/automation_pack.md`
- `.codex/orchestrator/automation/*.md`
- `.codex/orchestrator/automation_memory.json`
- `.codex/orchestrator/automation_memory.md`
- `.codex/orchestrator/execution_bridge.json`
- `.codex/orchestrator/execution_bridge.md`
- `.codex/orchestrator/orchestration_run.json`
- `.codex/orchestrator/orchestration_run.md`
- `.codex/orchestrator/validation_report.json`
- `.codex/orchestrator/validation_report.md`

## Default lanes

- Implementation lane
- Tests and coverage lane
- Review and hardening lane
- Docs and handoff lane

## Boundaries

`Phase 2C` plans and tracks parallel lanes. It does not itself create Codex app
worktrees or spawn a persistent multi-agent runtime. The artifacts are designed
to make worktree or CLI fan-out repeatable and resumable.

`Phase 2D` adds dispatch/bootstrap artifacts. If the repo is in a git checkout,
the generated shell scripts can create `git worktree` lanes with a suggested
`codex/...` branch name and run the local setup bootstrap automatically.

`Phase 3A` adds role-aware prompt packs and a readiness gate so parallel lanes
can converge back into one milestone with an explicit merge-ready signal.

`Phase 3B` adds convergence artifacts that collect completed lane outcomes into
one merge/hardening brief before the milestone returns to the main loop.

`Phase 3C` adds post-convergence merge orchestration so the milestone returns to
the main loop only after a fresh verify/review/hardening pass on the merged state.

`Phase 4A` adds a fleet supervisor layer that recommends the next best lane action
and keeps a milestone-level supervisory view over the entire track set.

`Phase 4B` adds escalation and recovery playbooks for blocked lanes and failing
post-merge cycles so the supervisor can point to a concrete recovery path.

`Phase 5A` adds a report-first automation cycle that refreshes verification,
review, readiness, convergence, supervisor, escalation, and optional merge
artifacts in one safe recurring run.

`Phase 5B` adds reusable recurring automation profiles and prompt packs so the
supervisory state can be turned into reviewed Codex app automations without
writing automation config directly.

`Phase 5C` adds recurring finding memory so the automation layer can distinguish
new issues from known recurring ones and report resolved items explicitly.

`Phase 6A` adds a supervisor-to-execution bridge so the next recommended action
is paired with concrete commands, inputs, and outputs for the next operator or lane.

`Phase 6B` adds semi-automatic orchestration so safe actions such as planning tracks,
starting lanes, preparing convergence, running merge gates, and archiving can be
executed directly while blocker-resolution actions still stop for human review.

`Phase 7A` adds shared action contracts plus a validation layer that checks
supervisor, bridge, and orchestration alignment before the workflow is trusted on
a real project.
