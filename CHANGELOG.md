# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `dag_executor.config` module as the designated environment-access layer.
- Unit tests under `tests/unit/` covering the CLI, node runners
  (`base`, `agent`, `bash`, `loop`, `gate`), models, and config helper.
- `CHANGELOG.md` and expanded README (purpose, scope, quick start, architecture).
- `.hooks/pre-commit` log-discipline guard.

### Changed
- Routed loop fan-out environment construction through `config.child_env`
  instead of reading `os.environ` directly (behaviour unchanged).
- Added `encoding="utf-8"` to all `read_text`/`write_text` calls.
- `cli.app()` now annotated `-> NoReturn`; JSON output uses `ensure_ascii=False`.
- `tests/conftest.py` now enforces a virtual-environment guard.

## [0.1.0] - 2026-05-22

### Added
- Initial Phase 1 DAG execution engine: YAML loader, rustworkx-backed graph,
  layered executor, and agent/bash/script/loop/gate node runners.
