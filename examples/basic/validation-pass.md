# Run a Validation-Only Pass

## When to use

Use this workflow when:

- the repo already contains an implementation
- you want a verification and hardening pass
- you do not want new features or architecture expansion

## Prompt

```text
$big-project-orchestrator

Run a validation-only pass on this repository.
Do not add new features and do not expand the architecture.

Create a validation-focused milestone and check the current implementation as a user would.
Run:
- repository verification
- review/hardening
- targeted bugfixes only if real problems are found
- re-verification after each fix

Update status, handoff, decisions, and archive the validation cycle when complete.
Stop only if there is a real blocker or once the repo is verified clean.
```

## What the skill should check

- repo-native verification commands
- broken user-visible flows
- review and hardening findings
- gaps in the current implementation that cause real failures

## Expected outputs

- a validation-focused milestone in `.codex/orchestrator/`
- bugfixes only if they are required by the validation pass
- final status and handoff showing whether the repo is clean or blocked

## Notes

- this is a good workflow after a large autonomous build
- it is also a good pre-release or pre-commit quality pass
