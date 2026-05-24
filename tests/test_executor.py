# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import yaml
import pytest

from dag_executor.executor import DAGExecutorRunner
from dag_executor.loader import load_graph
from dag_executor.models import GraphSpec, NodeSpec, NodeType


def _spec(nodes: list[dict], goal: str = "test goal") -> GraphSpec:
    data = {"workflow_id": "exec-wf", "nodes": nodes}
    return load_graph(data, goal_text=goal)


def test_single_bash_node_succeeds(tmp_path):
    spec = _spec([{"id": "n1", "type": "bash", "command": "echo done"}])
    runner = DAGExecutorRunner(artifacts_dir=str(tmp_path))
    result = runner.run_graph(spec)
    assert result["status"] == "succeeded"


def test_single_bash_failure(tmp_path):
    spec = _spec([{"id": "n1", "type": "bash", "command": "false"}])
    runner = DAGExecutorRunner(artifacts_dir=str(tmp_path))
    result = runner.run_graph(spec)
    assert result["status"] == "failed"


def test_linear_chain_all_succeed(tmp_path):
    spec = _spec([
        {"id": "a", "type": "bash", "command": "echo a"},
        {"id": "b", "type": "bash", "command": "echo b", "depends_on": ["a"]},
    ])
    runner = DAGExecutorRunner(artifacts_dir=str(tmp_path))
    result = runner.run_graph(spec)
    assert result["status"] == "succeeded"


def test_skip_on_dep_failure(tmp_path):
    spec = _spec([
        {"id": "fail_node", "type": "bash", "command": "false"},
        {
            "id": "skip_node",
            "type": "bash",
            "command": "echo should_skip",
            "depends_on": ["fail_node"],
            "trigger_rule": "all_success",
        },
    ])
    runner = DAGExecutorRunner(artifacts_dir=str(tmp_path))
    result = runner.run_graph(spec)
    assert result["status"] == "failed"
    node_results = result["metadata"]["node_results"]
    skip_res = next(r for r in node_results if r["node_id"] == "skip_node")
    assert not skip_res["success"]


def test_parallel_layer_all_succeed(tmp_path):
    spec = _spec([
        {"id": "a", "type": "bash", "command": "echo a"},
        {"id": "b", "type": "bash", "command": "echo b"},
        {"id": "c", "type": "bash", "command": "echo c"},
    ])
    runner = DAGExecutorRunner(artifacts_dir=str(tmp_path))
    result = runner.run_graph(spec)
    assert result["status"] == "succeeded"
    assert result["metadata"]["evidence"]["nodes_run"] == 3


def test_all_done_trigger_runs_despite_failure(tmp_path):
    spec = _spec([
        {"id": "fail_node", "type": "bash", "command": "false"},
        {
            "id": "always_node",
            "type": "bash",
            "command": "echo always",
            "depends_on": ["fail_node"],
            "trigger_rule": "all_done",
        },
    ])
    runner = DAGExecutorRunner(artifacts_dir=str(tmp_path))
    result = runner.run_graph(spec)
    node_results = result["metadata"]["node_results"]
    always_res = next(r for r in node_results if r["node_id"] == "always_node")
    assert always_res["success"] is True


def test_run_from_yaml(tmp_path):
    data = {
        "workflow_id": "yaml-wf",
        "nodes": [{"id": "x", "type": "bash", "command": "echo yaml_ok"}],
    }
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text(yaml.dump(data))
    runner = DAGExecutorRunner(artifacts_dir=str(tmp_path))
    result = runner.run_from_yaml(str(yaml_file), goal_text="test")
    assert result["status"] == "succeeded"


def test_empty_graph_succeeds(tmp_path):
    spec = _spec([])
    runner = DAGExecutorRunner(artifacts_dir=str(tmp_path))
    result = runner.run_graph(spec)
    assert result["status"] == "succeeded"
    assert result["metadata"]["evidence"]["nodes_run"] == 0


def test_runtime_result_schema_fields(tmp_path):
    spec = _spec([{"id": "n", "type": "bash", "command": "echo"}])
    runner = DAGExecutorRunner(artifacts_dir=str(tmp_path))
    result = runner.run_graph(spec)
    for field in (
        "schema_version", "contract_kind", "invocation_id", "runtime_name",
        "runtime_kind", "status", "started_at", "finished_at",
    ):
        assert field in result
