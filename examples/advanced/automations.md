# Report-First Automations

## When to use

Use this workflow when you want the skill to run recurring maintenance or reporting passes without changing code by default.

## What it is

The skill can refresh verification, review, supervision, escalation, and automation-ready reports in a safe report-first mode.

## Prompt

```text
$big-project-orchestrator

Report-only run.
Refresh verification, review, supervisor, escalation, and handoff artifacts for this repo.
Do not edit code.
Summarize blockers, risky files, and the next recommended action.
```

## Good recurring use cases

- nightly verification
- weekly release-readiness audit
- branch drift review
- track fleet supervision

## Notes

- this is advanced because it is most useful after the repo already has a stable workflow
- for real recurring jobs, pair it with Codex app automations
