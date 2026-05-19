# Contributing to DAGExecutor

DAGExecutor is the DAG-based workflow executor for the platform. It drives multi-node AI task graphs with topological scheduling, concurrent layer execution, and file-based human gate approval.

## Before You Start

- Check open issues to avoid duplicate work
- For significant changes, open an issue first to discuss the approach
- All contributions must pass the test suite and linter before merging

## Development Setup

```bash
git clone https://github.com/ProtocolWarden/DAGExecutor.git
cd DAGExecutor
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Requires Python 3.11+.

## Running Tests

```bash
.venv/bin/python -m pytest tests/ -v
```

## Invariants

- **D1**: `goal_text` from the ExecutionRequest must reach agent nodes verbatim (no wrapping, no rewriting).
- Cycle detection must fire before execution begins.
- Gate nodes must only advance (`approved`) or halt (`rejected`) — no silent skip.
