# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import pytest
import yaml

from dag_executor.loader import LoaderError, load_graph, load_graph_file
from dag_executor.models import NodeType, TriggerRule


def _graph(nodes: list[dict], **kw) -> dict:
    return {"workflow_id": "test-wf", "nodes": nodes, **kw}


def test_valid_single_bash_node():
    data = _graph([{"id": "step1", "type": "bash", "command": "echo hi"}])
    spec = load_graph(data)
    assert spec.workflow_id == "test-wf"
    assert len(spec.nodes) == 1
    assert spec.nodes[0].type == NodeType.BASH


def test_missing_workflow_id_raises():
    with pytest.raises(LoaderError, match="workflow_id"):
        load_graph({"nodes": []})


def test_unknown_node_type_raises():
    data = _graph([{"id": "x", "type": "unknown_type"}])
    with pytest.raises(LoaderError, match="Unknown node type"):
        load_graph(data)


def test_duplicate_node_id_raises():
    data = _graph([
        {"id": "dup", "type": "bash", "command": "echo 1"},
        {"id": "dup", "type": "bash", "command": "echo 2"},
    ])
    with pytest.raises(LoaderError, match="Duplicate node id"):
        load_graph(data)


def test_unknown_dep_ref_raises():
    data = _graph([
        {"id": "a", "type": "bash", "command": "echo", "depends_on": ["does_not_exist"]},
    ])
    with pytest.raises(LoaderError, match="unknown node"):
        load_graph(data)


def test_empty_nodes_list_ok():
    data = _graph([])
    spec = load_graph(data)
    assert spec.nodes == []


def test_gate_missing_message_raises():
    data = _graph([{"id": "approval", "type": "gate"}])
    with pytest.raises(LoaderError, match="gate_message"):
        load_graph(data)


def test_gate_with_message_ok():
    data = _graph([{"id": "ok_gate", "type": "gate", "gate_message": "Please approve"}])
    spec = load_graph(data)
    assert spec.nodes[0].gate_message == "Please approve"


def test_loop_with_items_from_ok():
    data = _graph([{
        "id": "fanout",
        "type": "loop",
        "items_from": "$prev.output",
        "command": "echo $ITEM",
    }])
    spec = load_graph(data)
    assert spec.nodes[0].items_from == "$prev.output"


def test_loop_without_command_or_items_raises():
    data = _graph([{"id": "bad_loop", "type": "loop"}])
    with pytest.raises(LoaderError, match="command or items_from"):
        load_graph(data)


def test_trigger_rule_parsed():
    data = _graph([{
        "id": "a",
        "type": "bash",
        "command": "echo",
        "trigger_rule": "all_done",
    }])
    spec = load_graph(data)
    assert spec.nodes[0].trigger_rule == TriggerRule.ALL_DONE


def test_goal_text_injected():
    data = _graph([])
    spec = load_graph(data, goal_text="build a thing")
    assert spec.goal_text == "build a thing"


def test_load_graph_file(tmp_path):
    yaml_data = {
        "workflow_id": "file-wf",
        "nodes": [{"id": "n1", "type": "bash", "command": "true"}],
    }
    p = tmp_path / "graph.yaml"
    p.write_text(yaml.dump(yaml_data))
    spec = load_graph_file(str(p))
    assert spec.workflow_id == "file-wf"
