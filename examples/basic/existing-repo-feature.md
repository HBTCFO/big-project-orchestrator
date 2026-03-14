# Add a Large Feature to an Existing Repo

## When to use

Use this workflow when:

- the repo already contains code
- you need a multi-file feature, migration, or major refactor
- you want reviewable milestones instead of one large unstructured run

## Starting point

Typical starting state:

- an existing repo already builds or mostly builds
- the user has a large task, not a tiny patch
- the work should stay inside a controlled scope

## Planning-first prompt

```text
$big-project-orchestrator

This is an existing repository.
I need a large feature added without losing control of scope.

First, create a planning-first milestone breakdown for this feature.
Do not code until the active milestone has:
- scope
- non-goals
- acceptance criteria
- validation commands
- risks

Then implement only the active milestone.
After implementation, run verification and review/hardening.
Repair safe local failures if needed.
Update status, handoff, decisions, and todo after each milestone.

Do not expand into unrelated refactors unless they are required to complete the active milestone safely.
```

## Autonomous follow-up

```text
The milestone plan looks good.
Now continue in autonomous mode through the remaining milestones.
Do not stop between milestones unless there is a real blocker.
```

## What the skill should do

- map the feature into milestone-sized slices
- keep diffs narrow and milestone-scoped
- reuse repo-native verification whenever possible
- avoid unrelated cleanup unless it is required for safe completion

## Expected outputs

- milestone-scoped diffs instead of one giant change
- updated `.codex/orchestrator/` planning artifacts
- verification and review after each stage
- archived milestone history as the feature advances

## Notes

- this example is useful for features, migrations, stabilization pushes, and large bugfix waves
- if the repo already has strong test commands, the skill should prefer them over generic verification
