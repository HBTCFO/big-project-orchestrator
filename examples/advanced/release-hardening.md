# Release Hardening

## When to use

Use this workflow when implementation is mostly done and you want a focused pre-release sweep instead of more feature work.

## Prompt

```text
$big-project-orchestrator

Run a release-hardening pass for the current branch.
Do not add new features.
Focus on verification, review, docs drift, risky files, missing tests, and release blockers.
Fix only real release issues that are safe to address inside this pass.
Update status and handoff for a release decision at the end.
```

## What the skill should do

- run repo-native verification
- identify release blockers and missing coverage
- review risky files and docs drift
- repair safe release issues
- produce a clear final release-readiness summary

## Notes

- this is advanced because it assumes the feature work is already substantially complete
