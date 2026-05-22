# Log

## 2026-05-21 — Add closing fence to console-context block

Added <!-- /console-context --> end marker so OperatorConsole only replaces its
managed block and leaves repo-owned content below it untouched.

## 2026-05-19 — ADR 0006 Phase 2: wire safe_run() in nodes/base.py

- Replaced subprocess.run(shell=True) in run_subprocess() with core_runner.process.safe_run().
- run_subprocess() now accepts list[str] | str; strings are split via shlex.split() (no shell features).
- agent.py _build_claude_cmd/_build_codex_cmd now return list[str] directly (removed shlex.quote + join).
- script.py uses [python, script_path] list form directly.
- bash.py and loop.py unchanged — strings flow through shlex.split transparently.
- Added core-runner dep to pyproject.toml; conftest.py adds ExecutorRuntime/src to sys.path.
- 108 tests pass.

## 2026-05-18

- Phase 1 initial build. All source modules written. Tests written against mocked rxp/cxrp contracts.
- D1 invariant enforced in `nodes/agent.py`: goal_text always goes to `--message`, node command appended as `--append-system-prompt`.
- RuntimeResult constructed directly (dataclass-compatible dict) to avoid rxp import at test time.
- `graph.py` uses rustworkx PyDiGraph for cycle detection and topological ordering.

## 2026-05-19 — ADR 0005 Phase 5: worker_backend abstraction in agent nodes

Added worker_backend param to AgentNodeRunner.run() and DAGExecutorRunner.__init__().
"codex_cli" routes to codex CLI subprocess; default "claude_code" uses existing claude path.
DAGExecutorRunner passes worker_backend through run_kwargs for AGENT node type only.
55 tests pass.


## 2026-05-22 — P5: Revert to CL shim (manifest-cognition work order)

Per PlatformDeployment/docs/architecture/adr/0002-work-order-manifest-cognition.md Phase 5:

- Deleted `.context/` (config.yaml + templates/) — cognition now hosted by anchoring manifest.
- Replaced `.claude/hooks/pre_tool_use.sh` (~330 lines) and `.claude/hooks/stop.sh` (~116 lines) with thin ~10-line shims that exec `cl hook <event>`. Logic lives in the CL package.
- Updated CLAUDE.md "Cognition Lifecycle" section to reflect library-consumer posture; sessions must `eval $(cl session start <manifest>)` before tools fire, else hooks fail closed.
- Cleaned `.gitignore` of stale `.context/*` rules.
- Confirmed zero CL imports in src/ (executor never coupled to CL Python API).

Branch: feat/p5-revert-to-shim. Staged, not committed.
