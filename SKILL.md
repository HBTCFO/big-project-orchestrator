---
name: big-project-orchestrator
description: Coordinate medium-to-large software projects locally in Codex app or Codex CLI using durable markdown plans, milestone-by-milestone execution, reviewable diffs, worktree-friendly workflows, repeatable verification, and structured handoffs. Use when the task is a multi-file feature, migration, major refactor, subsystem build, stabilization push, release hardening, or any project that should be planned, implemented, validated, and archived in cycles. Do not use for trivial one-file edits, quick Q&A, or tiny bug fixes.
---

# Big Project Orchestrator

A Codex-native, local-first orchestration workflow for large projects on macOS. This skill is inspired by the best parts of g3's planning mode, coach/player loop, and studio/worktree workflow, but adapted to Codex's native strengths: local shell execution, app worktrees, skills, automations, and optional CLI multi-agent support.

## Core operating model

Treat large work as a loop, not as one giant prompt:

1. Freeze or refine the requirement.
2. Turn it into one active milestone with explicit acceptance criteria.
3. Implement only that milestone.
4. Run validation.
5. Repair failures before moving on.
6. Update status, handoff notes, and decision log.
7. Archive the cycle and start the next milestone.

Use durable project memory in files, not only in chat. The canonical working files live in `.codex/orchestrator/`.

## When to use this skill

Use this skill when the user asks for any of the following:

- Build a new product or subsystem over multiple milestones.
- Run a large refactor or migration with checkpoints.
- Split a large repo task into reviewable worktree-sized chunks.
- Stabilize a messy branch with structured validation and handoff.
- Run repeatable report-first maintenance such as regression audits, drift checks, release readiness, docs sync, or quality sweeps.
- Recreate a g3-style planning loop in Codex without external LLM APIs.

Do **not** use this skill for:

- Small edits that can be finished in one pass.
- Simple code explanations with no implementation.
- One-off shell tasks with no durable artifacts needed.

## Ground rules

- Stay local-first. Do not introduce external LLM providers, external agent runtimes, or network dependencies unless the user explicitly asks.
- Prefer Codex app **Worktree** threads for parallel implementation tracks.
- Prefer Codex app **Automations** only for stable, report-first recurring jobs.
- Prefer the repo's own build, lint, test, and typecheck commands when known.
- Keep diffs narrow and milestone-scoped.
- Update the durable files after each meaningful step.
- If validation fails, repair before archiving or handing off.
- Do not silently skip validation on a code-changing milestone.

## Required durable files

The orchestrator workspace is `.codex/orchestrator/` and should contain at least:

- `new_requirements.md` — candidate or newly refined work.
- `current_requirements.md` — the one active milestone being implemented.
- `todo.md` — concrete checklist for the active milestone.
- `decisions.md` — important decisions, tradeoffs, rejected options.
- `status.md` — current state, what changed, what remains blocked.
- `handoff.md` — concise next-step note for the next thread or reviewer.
- `planner_history.txt` — append-only lifecycle log.
- `completed/` — timestamped archived cycles.
- Optional: `verification.commands.sh` and `setup.commands.sh` for repo-specific commands.

## First-run bootstrap

When this skill is used in a repo for the first time:

1. Resolve the skill directory from the location of this `SKILL.md`.
2. Initialize the workspace:

   ```bash
   python3 <skill-dir>/scripts/init_orchestrator.py --repo "$PWD"
   ```

3. If the user wants repo-native guidance, install the optional repo templates:

   ```bash
   bash <skill-dir>/scripts/install_repo_templates.sh --repo "$PWD"
   ```

4. Read:
   - `.codex/orchestrator/new_requirements.md`
   - `.codex/orchestrator/current_requirements.md`
   - `.codex/orchestrator/todo.md`
   - `.codex/orchestrator/decisions.md`
   - `.codex/orchestrator/status.md`

5. If the task is new and `new_requirements.md` is populated but `current_requirements.md` is not approved yet, refine the requirement first instead of coding immediately.

## Autonomous project mode

Use autonomous mode when the user provides a large spec and explicitly wants the
project driven milestone-by-milestone with minimal pauses.

Primary entry point:

```bash
python3 <skill-dir>/scripts/run_autonomous_cycle.py --repo "$PWD" --resume
```

For greenfield repos that only contain `spec.md` or `requirements.md`, allow
local skeleton generation:

```bash
python3 <skill-dir>/scripts/run_autonomous_cycle.py --repo "$PWD" --allow-structure-generation --resume
```

In this mode:

- initialize or resume `.codex/orchestrator/state.json`
- derive milestones from the input spec
- activate one milestone at a time
- run verification after implementation
- run a mandatory review/hardening pass before archive
- attempt safe local repairs
- archive completed milestones
- continue unless a real blocker is reached

For large milestones that need parallel worktree lanes, also use:

```bash
python3 <skill-dir>/scripts/plan_tracks.py --repo "$PWD"
```

or run autonomous mode with track planning enabled:

```bash
python3 <skill-dir>/scripts/run_autonomous_cycle.py --repo "$PWD" --plan-tracks --resume
```

To emit worktree/bootstrap dispatch artifacts at the same time:

```bash
python3 <skill-dir>/scripts/run_autonomous_cycle.py --repo "$PWD" --plan-tracks --generate-dispatch --resume
```

Or generate them directly from an existing track plan:

```bash
python3 <skill-dir>/scripts/generate_track_dispatch.py --repo "$PWD"
```

Generate ready-to-use prompts for each track:

```bash
python3 <skill-dir>/scripts/generate_track_prompts.py --repo "$PWD"
```

And evaluate whether the parallel lanes are ready to merge:

```bash
python3 <skill-dir>/scripts/evaluate_track_readiness.py --repo "$PWD"
```

When the lanes are complete, prepare the convergence brief:

```bash
python3 <skill-dir>/scripts/prepare_track_convergence.py --repo "$PWD"
```

Then run post-convergence verify/review/hardening before archive:

```bash
python3 <skill-dir>/scripts/orchestrate_track_merge.py --repo "$PWD"
```

To get a fleet-level recommendation for which lane or gate to handle next:

```bash
python3 <skill-dir>/scripts/run_track_supervisor.py --repo "$PWD"
```

To turn the recommendation into a concrete execution handoff:

```bash
python3 <skill-dir>/scripts/generate_execution_bridge.py --repo "$PWD"
```

To execute the next safe orchestration step automatically:

```bash
python3 <skill-dir>/scripts/orchestrate_next_action.py --repo "$PWD"
```

To validate orchestration state invariants before a real project:

```bash
python3 <skill-dir>/scripts/validate_orchestrator_state.py --repo "$PWD"
```

If a lane blocks or post-merge hardening fails, generate the recovery playbook:

```bash
python3 <skill-dir>/scripts/generate_escalation_playbook.py --repo "$PWD"
```

For recurring report-first runs, refresh the full supervisory stack in one safe pass:

```bash
python3 <skill-dir>/scripts/run_automation_cycle.py --repo "$PWD"
```

Then generate ready-to-use recurring automation profiles:

```bash
python3 <skill-dir>/scripts/generate_automation_pack.py --repo "$PWD"
```

Do not stop between phases unless:

- the project is complete
- safe repair attempts are exhausted
- a required secret, credential, or external dependency is missing
- the spec is contradictory enough to block safe progress
- the local environment cannot continue

## Requirement refinement workflow

Before implementation, turn vague asks into a milestone that has:

- scope
- non-goals
- acceptance criteria
- validation commands
- important constraints
- user-visible deliverables
- explicit "done when" conditions

When `new_requirements.md` is ready to become the active milestone, promote it:

```bash
python3 <skill-dir>/scripts/promote_requirements.py --repo "$PWD" --title "<short milestone title>"
```

Then update `todo.md` with a concrete checklist.

## Implementation workflow

For each milestone:

1. Read `current_requirements.md`, `todo.md`, and `decisions.md`.
2. Map the files, modules, or packages affected.
3. If the milestone is large, split it into 2–6 reviewable subtracks.
4. In the Codex app:
   - prefer **Worktree** mode for subtracks or risky changes.
   - keep one thread per subtrack.
5. In Codex CLI:
   - if experimental multi-agent is enabled, use the configured roles (`explorer`, `reviewer`, `worker`, `monitor`) for focused parallel work.
6. Implement only the active milestone.
7. Run verification.
8. Update `status.md`, `handoff.md`, `decisions.md`, and `todo.md`.
9. Archive the cycle when the milestone is complete.

## Verification workflow

Always check for repo-specific commands first.

If `.codex/orchestrator/verification.commands.sh` exists, run it:

```bash
bash .codex/orchestrator/verification.commands.sh
```

Otherwise run the bundled verifier:

```bash
bash <skill-dir>/scripts/verify_repo.sh "$PWD"
```

The verifier supports common Rust, Node, Python, Go, Java, and Make-based repos. If the repo is unusual, create or update `.codex/orchestrator/verification.commands.sh` instead of forcing bad autodetection.

## Worktree strategy

### In the Codex app

Use built-in worktrees for:

- parallel feature branches
- refactor vs stabilization split
- implementation vs review threads
- long-running report-first automations

Recommended pattern:

- Thread A: main implementation
- Thread B: tests / coverage
- Thread C: reviewer / hardening
- Thread D: docs / migration notes

Keep each thread aligned to the same `current_requirements.md`, but give each a distinct checklist slice in `todo.md`.

### In the Codex CLI

If you need batch fan-out reviews, convert checklist items to CSV:

```bash
python3 <skill-dir>/scripts/split_work_items.py --input .codex/orchestrator/todo.md --output /tmp/work-items.csv
```

Then ask Codex to process it with `spawn_agents_on_csv`.

## Handoff discipline

Before you stop or ask another thread to continue, update:

- `status.md` with what is finished, in progress, and blocked
- `handoff.md` with the exact next best action
- `decisions.md` with any important choice that should not be re-litigated
- `planner_history.txt` with a short timestamped event

Use the status renderer when useful:

```bash
python3 <skill-dir>/scripts/render_status.py --repo "$PWD"
```

## Archiving a completed milestone

When a milestone is complete and verified:

```bash
python3 <skill-dir>/scripts/archive_cycle.py --repo "$PWD" --label "<short milestone title>"
```

This archives the active files into `.codex/orchestrator/completed/<timestamp>-<label>/`, appends to `planner_history.txt`, and resets the workspace for the next cycle.

## Codex app setup recommendations

Use the Codex app's Local Environments feature to run the bundled setup script automatically when a new worktree starts:

```bash
bash <skill-dir>/scripts/setup_workspace.sh "$PWD"
```

Good recurring actions for the app top bar:

- run tests
- run lint
- run typecheck
- render status
- package release notes

## Automation recommendations

Only automate stable, report-first workflows. Good examples:

- nightly verification report
- branch drift audit
- weekly release-readiness review
- docs drift report
- coverage gap report

In automation prompts, explicitly invoke this skill with `$big-project-orchestrator` and say whether the run is **report-only** or allowed to edit.

Prefer `run_automation_cycle.py` for recurring local automations. It refreshes verification, review, track readiness, convergence, supervisor, and escalation artifacts without attempting repair or code edits.

Use `generate_automation_pack.py` after that when you want durable prompt/contracts for Codex app scheduled runs without touching the user's actual automation config yet.

`Phase 5C` adds `update_automation_memory.py`, which records recurring finding memory so each report can distinguish new issues from already-known ones.

`Phase 6A` adds `generate_execution_bridge.py`, which maps the current supervisor recommendation to concrete commands, inputs, and expected outputs for the next lane, merge, recovery, or archive step.

`Phase 6B` adds `orchestrate_next_action.py`, which can execute the next safe orchestration step automatically and stops with `needs_human` on blocker-recovery paths that should not be automated blindly.

`Phase 7A` adds `validate_orchestrator_state.py` plus shared action contracts, reducing duplication between the supervisor, execution bridge, and orchestration runner while catching stale or contradictory state early.

## Quality bar

A milestone is not done until all of the following are true:

- scope matches `current_requirements.md`
- user-visible behavior matches the stated acceptance criteria
- verification ran and passed, or failures are explicitly documented with rationale
- `status.md` and `handoff.md` are current
- diff is reviewable
- next milestone is clearer because of the artifacts left behind

## Helper files to consult

Open these when needed:

- `references/WORKFLOW.md` — detailed operating procedures
- `references/AUTONOMOUS_MODE.md` — autonomous cycle rules, repair policy, resume behavior
- `references/MULTI_TRACK_MODE.md` — worktree and parallel-lane planning artifacts
- `references/G3_MAPPING.md` — how this maps to g3 concepts
- `references/AUTOMATIONS.md` — safe automation patterns
- `assets/templates/` — starter files and repo templates
- `assets/repo/.codex/` — optional CLI/app support files

## Typical user prompts that should trigger this skill

- "Help me build this as a big project with milestones and durable planning."
- "Use a g3-style planning loop for this repo, but keep it in Codex."
- "Split this migration into worktree-friendly phases and keep status files updated."
- "Create a repeatable plan / implement / validate / archive workflow for this codebase."
- "Run this as a local long-horizon project without external LLM APIs."

## Practical boundaries

This skill assumes:

- the user wants local work on their machine
- Codex app or Codex CLI is the only LLM surface
- the repo is available on disk
- Git is preferred for worktree-based isolation
- multi-agent is optional and currently CLI-first
