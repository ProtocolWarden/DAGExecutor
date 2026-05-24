# DAGExecutor

DAG execution engine for the owned execution-topology layer. Phase 1 implementation.

Accepts a YAML graph definition and executes it as a directed acyclic graph (DAG),
replacing Archon as OperationsCenter's execution backend.

## What this repo is

- A thin, library-first execution backend that turns a declarative YAML
  workflow into a layered DAG and runs each node as a process-group-safe
  subprocess (via `core_runner.process.safe_run`).
- A small set of node runners — `agent`, `bash`, `script`, `loop`, `gate` —
  exposed both as a Python API (`DAGExecutorRunner`) and a CLI (`dag-executor`).
- An emitter of a plain-dict result shaped like an RxP `RuntimeResult`, so
  callers with RxP installed can hydrate a typed contract from it.

## What this repo is not

- Not an agent or LLM orchestrator: it shells out to whatever `agent`-node
  command is configured and does not embed planning, retries, or model logic.
- Not a scheduler or long-running service: each `run` executes one graph to
  completion and exits.
- Not a workflow editor or UI: gates are file-based checkpoints, not a
  human-in-the-loop interface.
- Not the owner of contract types: RxP/CxRP define the contracts; this repo
  only mirrors the result shape.

## Quick start

```
pip install -e ".[dev]"

# Run a workflow YAML
dag-executor run graph.yaml --goal "implement feature X"
```

Programmatic use:

```python
from dag_executor import DAGExecutorRunner

runner = DAGExecutorRunner(artifacts_dir="/tmp/artifacts")
result = runner.run_from_yaml("graph.yaml", goal_text="implement feature X")
print(result["status"])  # "succeeded" | "failed"
```

## Architecture

The execution pipeline is a short, explicit chain:

1. **Loader** (`loader.py`) — parses and validates YAML into a `GraphSpec`
   of `NodeSpec`s (`models.py`).
2. **Graph** (`graph.py`) — builds a rustworkx DAG, rejects cycles, and
   exposes topological *layers* (sets of nodes runnable in parallel).
3. **Executor** (`executor.py`) — walks layers in order, evaluates each
   node's `trigger_rule` against completed dependencies, runs the layer
   (concurrently when it has >1 node), and aggregates evidence.
4. **Node runners** (`nodes/`) — one runner per node type. `base.py` holds
   the shared `run_subprocess` helper and command resolution; `variables.py`
   performs `$VAR`/`$node.output` substitution.
5. **Config** (`config.py`) — the single environment-access layer; node
   runners never read `os.environ` directly.

### Node types

- `agent` — Claude Code (or Codex CLI) subprocess (D1: goal_text reaches
  `--message` verbatim)
- `bash` — shell command
- `script` — Python script written to a temp file and executed
- `loop` — static iteration until `DONE`, or dynamic fan-out over `items_from`
- `gate` — file-based human approval checkpoint

## Development

```
.venv/bin/python -m pytest -q
```

Tests run inside this project's `.venv` (enforced by a conftest venv guard).
