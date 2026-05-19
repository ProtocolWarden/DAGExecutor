# Log

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
