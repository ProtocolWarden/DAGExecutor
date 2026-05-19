# DAGExecutor

DAG execution engine for the owned execution topology layer. Phase 1 implementation.

Accepts a YAML graph definition and executes it as a directed acyclic graph (DAG), replacing Archon as OperationsCenter's execution backend.

## Install

```
pip install -e ".[dev]"
```

## Usage

```
dag-executor run graph.yaml --goal "implement feature X"
```

## Node types

- `agent` — Claude Code subprocess (D1: goal_text reaches `--message` verbatim)
- `bash` — shell script
- `script` — Python script
- `loop` — iteration with optional dynamic fan-out
- `gate` — human approval checkpoint (file-based)
