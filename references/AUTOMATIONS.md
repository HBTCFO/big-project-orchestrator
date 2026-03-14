# Safe automation patterns

Use automations only after a workflow is stable.

## Rule of thumb

Prefer report-only automations first. Only allow editing automations after:
- the repo-specific validation commands are correct
- the scope is narrow
- the first few runs were reviewed manually

Recommended recurring entrypoint:

```bash
python3 <skill-dir>/scripts/run_automation_cycle.py --repo "$PWD"
```

Recommended profile generator:

```bash
python3 <skill-dir>/scripts/generate_automation_pack.py --repo "$PWD"
```

## Good automation prompts

### Nightly verification

```text
$big-project-orchestrator

Report-only run. Refresh the orchestrator status, run verification, summarize failures and risky areas, and do not edit code.
```

Or run the local automation-safe supervisory cycle directly:

```bash
python3 <skill-dir>/scripts/run_automation_cycle.py --repo "$PWD"
```

Then materialize the recurring profiles and prompts:

```bash
python3 <skill-dir>/scripts/generate_automation_pack.py --repo "$PWD"
```

### Weekly branch drift audit

```text
$big-project-orchestrator

Report-only run. Compare the working branch with main, identify drift, merge-risk hotspots, stale docs, and tests most likely to fail after rebase.
```

### Release readiness

```text
$big-project-orchestrator

Report-only run. Review release readiness for the current branch, list blockers, missing tests, docs gaps, and unresolved risks, then update status and handoff files.
```

### Coverage improver (guarded)

```text
$big-project-orchestrator

Start in report-only mode. Find the biggest test coverage gaps for the current milestone, propose the top 3 missing tests, and wait for approval before editing.
```

## Editing automations

Only allow code changes in automations when all of the following are true:

- the repo has exact `verification.commands.sh`
- the change surface is narrow
- the sandbox settings are intentional
- the diff will be reviewed afterward

`run_automation_cycle.py` is intentionally report-only. It refreshes artifacts and recommendations, but it never enters repair or implementation mode.

`generate_automation_pack.py` is also non-destructive. It only writes reusable local prompt/contracts under `.codex/orchestrator/automation*` so you can create Codex app automations from reviewed artifacts instead of improvising prompts each time.

`update_automation_memory.py` maintains recurring issue memory under `.codex/orchestrator/automation_memory.*` so nightly or weekly runs can say which findings are new, which are recurring, and which were resolved since the previous run.

`generate_execution_bridge.py` complements this by turning the current supervisor recommendation into a concrete next-step handoff after a report-only run, without performing the edit itself.
