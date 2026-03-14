# Contributing

## Scope

This repository contains a Codex skill bundle. Changes should keep the bundle usable as a local-first, deterministic helper for Codex app and Codex CLI.

## Before you change anything

- Read [SKILL.md](./SKILL.md) first.
- Keep the skill local-first. Do not add external APIs or network dependencies unless the change explicitly requires them.
- Prefer improving the existing scripts and templates over adding parallel systems.

## Repository rules

- Do not commit generated junk such as `.DS_Store`, `__pycache__`, or `*.pyc`.
- Keep examples and docs aligned with the actual script entry points.
- Preserve backward-compatible install paths when possible: prefer `.codex/skills`, but do not break legacy `.agents/skills` fallback behavior.

## Recommended checks

Run these before opening a PR or publishing a release:

```bash
python3 -m py_compile scripts/*.py
bash -n install.sh
bash -n scripts/install_repo_templates.sh
bash -n scripts/setup_workspace.sh
bash -n scripts/verify_repo.sh
```

If you changed templates or install behavior, also test a local install into a throwaway repo or personal skills directory.

## Documentation expectations

Any user-facing workflow change should update:

- [README.md](./README.md)
- [SKILL.md](./SKILL.md)
- the relevant file in [references/](./references)

## Release expectations

- Keep the bundle self-contained.
- Keep install instructions accurate for both repo-local and user-wide installs.
- Prefer small, auditable changes over large undocumented rewrites.
