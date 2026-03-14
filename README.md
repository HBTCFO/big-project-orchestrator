# Big Project Orchestrator

A Codex skill for medium-to-large software projects that need planning, milestone-by-milestone execution, verification, repair loops, durable handoffs, and optional worktree-based parallelization.

It is built for **Codex app** and **Codex CLI**, keeps everything local-first, and ships as a self-contained skill bundle.

## Why this exists

Large projects degrade fast when all context lives in chat. This skill moves the project state into durable files under `.codex/orchestrator/` and treats work as a repeatable loop:

1. refine or freeze the requirement
2. activate one milestone
3. implement only that milestone
4. verify
5. repair if needed
6. update status, handoff, and decisions
7. archive the cycle and continue

It is **g3-inspired**, but **Codex-native**:

- g3 planning mode -> durable `.codex/orchestrator/` project memory
- g3 coach/player -> optional Codex CLI multi-agent roles
- g3 studio/worktrees -> Codex app worktree threads and dispatch artifacts
- g3 audit/history -> explicit status, handoff, archive, and validation reports

## Good fit

Use `big-project-orchestrator` when you want to:

- build a new subsystem or product over multiple milestones
- run a large refactor or migration with checkpoints
- split a big task into reviewable tracks
- stabilize a messy branch with repeatable verification
- run report-first audits, release hardening, or regression sweeps

Do not use it for trivial one-file edits or simple Q&A.

## Requirements

- macOS or another Unix-like environment with `bash` and `python3`
- Codex app or Codex CLI
- local filesystem access to the repo you want to orchestrate

No external APIs or third-party LLM runtimes are required.

## Install

### Repo-local install

```bash
bash install.sh --repo /path/to/your/repo
```

This installs the skill into the repo-local skills directory:

```text
/path/to/your/repo/.codex/skills/big-project-orchestrator
```

### User-wide install

```bash
bash install.sh --user
```

This installs the skill into your personal Codex skills directory, typically:

```text
$HOME/.codex/skills/big-project-orchestrator
```

Older Codex setups may still use `.agents/skills`; `install.sh` detects that layout automatically.

Restart Codex if the skill does not appear immediately.

## Optional repo support files

After installing the skill, you can bootstrap repo helper files with:

```bash
bash .codex/skills/big-project-orchestrator/scripts/install_repo_templates.sh --repo .
```

This adds:

- `.codex/orchestrator/` starter files
- optional `.codex/config.toml`
- optional `.codex/agents/*.toml`
- `AGENTS.md` if the repo does not already have one
- `AGENTS.big-project-orchestrator.snippet.md` if `AGENTS.md` already exists

## Quick start in Codex app

1. Open the repo in Codex app.
2. Start a new thread.
3. Invoke the skill:

   ```text
   $big-project-orchestrator
   ```

4. Give it a milestone-oriented prompt.

Example:

```text
$big-project-orchestrator

Initialize the orchestrator workspace for this repo, refine my request into a first milestone, do not code until the milestone has acceptance criteria and validation commands, then implement only milestone 1 and update status and handoff files.
```

## Quick start in Codex CLI

Start Codex inside your repo and use the same invocation:

```text
$big-project-orchestrator

Initialize the orchestrator workspace, create a milestone-based plan, implement only the active milestone, run verification, and update the durable project memory files before stopping.
```

## Examples

Basic examples:

- [Build from a large spec](./examples/basic/from-spec.md)
- [Add a large feature to an existing repo](./examples/basic/existing-repo-feature.md)
- [Run a validation-only pass](./examples/basic/validation-pass.md)

Advanced examples:

- [Multi-track and worktree execution](./examples/advanced/multi-track-worktrees.md)
- [Report-first automations](./examples/advanced/automations.md)
- [Escalation and recovery flows](./examples/advanced/escalation-recovery.md)
- [Release hardening](./examples/advanced/release-hardening.md)
- [Phase 1.5 / 2 planning](./examples/advanced/phase-2-planning.md)

## Autonomous mode

For a large spec where you want minimal pauses between milestones:

```bash
python3 .codex/skills/big-project-orchestrator/scripts/run_autonomous_cycle.py --repo "$PWD" --resume
```

For greenfield repos that only contain `spec.md` or `requirements.md`:

```bash
python3 .codex/skills/big-project-orchestrator/scripts/run_autonomous_cycle.py --repo "$PWD" --allow-structure-generation --resume
```

Optional helpers:

- `--plan-tracks` to split large milestones into parallel tracks
- `--generate-dispatch` to emit worktree/bootstrap dispatch artifacts

## Recommended Codex app setup

Useful worktree setup script:

```bash
bash .codex/skills/big-project-orchestrator/scripts/setup_workspace.sh "$PWD"
```

Useful action buttons:

- `bash .codex/skills/big-project-orchestrator/scripts/verify_repo.sh "$PWD"`
- `python3 .codex/skills/big-project-orchestrator/scripts/render_status.py --repo "$PWD"`

## Recommended automations

This skill also supports report-first recurring runs.

Example nightly verification prompt:

```text
$big-project-orchestrator

Report-only run. Refresh status, run the repo verification workflow, summarize failures and risky files, and do not edit code.
```

Example weekly hardening prompt:

```text
$big-project-orchestrator

Report-only run. Review the current branch against main, identify release blockers, missing tests, and docs drift, then update status and handoff notes.
```

## Customization points

Repo-specific verification script:

```text
.codex/orchestrator/verification.commands.sh
```

Repo-specific worktree setup script:

```text
.codex/orchestrator/setup.commands.sh
```

These let you override the generic bundled behavior with repo-native commands.

## Repository layout

- `SKILL.md` -> core skill behavior
- `install.sh` -> installer for repo-local or user-wide install
- `scripts/` -> deterministic orchestration helpers
- `references/` -> supporting operating docs
- `assets/templates/` -> durable project-memory templates
- `assets/repo/.codex/` -> optional Codex app / CLI config
- `agents/openai.yaml` -> skill metadata

## Limitations

- It is still a skill bundle, not a background daemon or native Codex runtime feature.
- Multi-agent behavior in Codex CLI remains optional and environment-dependent.
- For real external integrations, you still need repo-specific runtime wiring and credentials.

## Development

Recommended local checks:

```bash
python3 -m py_compile scripts/*.py
bash -n install.sh
bash -n scripts/install_repo_templates.sh
bash -n scripts/setup_workspace.sh
bash -n scripts/verify_repo.sh
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) for contribution rules.

## License

See [LICENSE.txt](./LICENSE.txt).
