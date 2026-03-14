# Escalation and Recovery Flows

## When to use

Use this workflow when the skill hits a real blocker, repeated post-merge failures, or a stuck track fleet.

## What it is

Instead of silently stalling, the skill can generate explicit recovery playbooks and execution handoffs that show what should be fixed next and whether the next step is safe to automate.

## Prompt

```text
$big-project-orchestrator

The current workflow is blocked.
Generate the escalation and recovery artifacts, explain the blocker clearly, and prepare the next safe action.
If the next action is safe, prepare an execution bridge.
If it requires human judgment, stop with a concrete recovery plan.
```

## Expected outputs

- escalation report
- supervisor recommendation
- execution bridge for the next safe step
- updated status and handoff notes

## Notes

- this is advanced because it matters only after the repo is already using autonomous or multi-track flows
