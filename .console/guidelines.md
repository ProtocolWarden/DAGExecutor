# Guidelines

## Branch policy

Never commit to `main` directly. Use feature branches. Pre-commit hook enforces `.console/log.md` updates.

## Style

- SPDX headers on every source file
- Line length 100 (ruff enforced)
- No print() in library code
- No docstrings on obvious functions
- `from __future__ import annotations` on all modules
- Dataclasses for models (not Pydantic)

## D1 invariant

`ExecutionRequest.goal_text` MUST reach agent nodes verbatim as `--message` argument to Claude Code.

## Contracts

- CxRP: `/home/dev/Documents/GitHub/CxRP`
- RxP: `/home/dev/Documents/GitHub/RxP` (package at `rxp/`, not `src/rxp/`)
