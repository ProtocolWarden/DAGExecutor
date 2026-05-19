# Log

## 2026-05-18

- Phase 1 initial build. All source modules written. Tests written against mocked rxp/cxrp contracts.
- D1 invariant enforced in `nodes/agent.py`: goal_text always goes to `--message`, node command appended as `--append-system-prompt`.
- RuntimeResult constructed directly (dataclass-compatible dict) to avoid rxp import at test time.
- `graph.py` uses rustworkx PyDiGraph for cycle detection and topological ordering.
