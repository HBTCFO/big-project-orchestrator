# Phase 1.5 / 2 Planning

## When to use

Use this workflow after a first product wave is complete and you want to plan the next one without starting implementation immediately.

## Prompt

```text
$big-project-orchestrator

Do a planning-only pass for the next product wave.
Read the current spec, decisions, and parked backlog.
Propose a Phase 1.5 / Phase 2 roadmap with milestones, dependencies, risks, and validation surfaces.
Do not start implementation yet.
Do not activate the next milestone without explicit confirmation.
```

## What the skill should do

- read the current project state and parked backlog
- separate near-term work from later ideas
- propose reviewable next-wave milestones
- record risks and dependencies before any coding begins

## Notes

- this is advanced because it makes sense only after a prior product slice already exists
