# Build From a Large Spec

## When to use

Use this workflow when:

- the repo is empty or nearly empty
- the main input is a large `spec.md` or `requirements.md`
- you want the skill to drive the work milestone-by-milestone with minimal pauses

## Starting point

Typical starting state:

- the repo contains `spec.md`
- there may be a few supporting reference files
- no significant implementation exists yet

## Prompt

```text
$big-project-orchestrator

In this repo there is a large spec in spec.md.
Run in autonomous project mode.

Work milestone-by-milestone until the project is complete.
Do not stop between milestones unless there is a real blocker.
For each milestone:
- implement only the active milestone
- run verification
- run review/hardening
- repair safe local failures if needed
- update status, handoff, decisions, and todo
- archive the completed cycle and continue

Use spec.md as the source of truth.
If there are reference docs, use them only as supporting context.
Do not expand scope beyond the spec unless the spec itself requires it.
```

## What the skill should do

- initialize `.codex/orchestrator/`
- derive a milestone plan from the spec
- activate the first milestone
- implement only the active milestone
- verify, review, and repair before advancing
- archive each completed cycle
- continue until done or blocked

## Expected outputs

- a populated `.codex/orchestrator/` workspace
- milestone history in `.codex/orchestrator/completed/`
- implementation changes in the repo
- verification and review artifacts for each cycle

## Notes

- this is the strongest example for greenfield work
- if a later phase needs credentials or another real external dependency, the skill should stop and report the blocker clearly
