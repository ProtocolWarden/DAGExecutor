# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import pytest

from dag_executor.graph import CyclicGraphError, DagGraph
from dag_executor.loader import load_graph


def _make(nodes: list[dict], **kw) -> dict:
    return {"workflow_id": "g-wf", "nodes": nodes, **kw}


def test_single_node_one_layer():
    spec = load_graph(_make([{"id": "a", "type": "bash", "command": "echo"}]))
    dag = DagGraph(spec)
    layers = dag.layers()
    assert len(layers) == 1
    assert layers[0][0].id == "a"


def test_linear_chain_two_layers():
    spec = load_graph(_make([
        {"id": "a", "type": "bash", "command": "echo"},
        {"id": "b", "type": "bash", "command": "echo", "depends_on": ["a"]},
    ]))
    dag = DagGraph(spec)
    layers = dag.layers()
    assert len(layers) == 2
    assert layers[0][0].id == "a"
    assert layers[1][0].id == "b"


def test_parallel_nodes_single_layer():
    spec = load_graph(_make([
        {"id": "a", "type": "bash", "command": "echo"},
        {"id": "b", "type": "bash", "command": "echo"},
        {"id": "c", "type": "bash", "command": "echo"},
    ]))
    dag = DagGraph(spec)
    layers = dag.layers()
    assert len(layers) == 1
    assert len(layers[0]) == 3


def test_cycle_detection_raises():
    # loader won't catch cycles — DagGraph must
    from dag_executor.models import GraphSpec, NodeSpec, NodeType
    spec = GraphSpec(
        workflow_id="cyclic",
        nodes=[
            NodeSpec(id="a", type=NodeType.BASH, depends_on=["b"]),
            NodeSpec(id="b", type=NodeType.BASH, depends_on=["a"]),
        ],
    )
    with pytest.raises(CyclicGraphError):
        DagGraph(spec)


def test_topological_order_respected():
    spec = load_graph(_make([
        {"id": "root", "type": "bash", "command": "echo"},
        {"id": "mid", "type": "bash", "command": "echo", "depends_on": ["root"]},
        {"id": "leaf", "type": "bash", "command": "echo", "depends_on": ["mid"]},
    ]))
    dag = DagGraph(spec)
    layers = dag.layers()
    ids_in_order = [layer[0].id for layer in layers]
    assert ids_in_order == ["root", "mid", "leaf"]


def test_empty_graph_no_layers():
    spec = load_graph(_make([]))
    dag = DagGraph(spec)
    layers = dag.layers()
    assert layers == [] or all(len(l) == 0 for l in layers)


def test_get_node_by_id():
    spec = load_graph(_make([{"id": "alpha", "type": "bash", "command": "echo"}]))
    dag = DagGraph(spec)
    node = dag.get_node("alpha")
    assert node.id == "alpha"


def test_diamond_dependency_layers():
    # a → b, a → c, b → d, c → d
    spec = load_graph(_make([
        {"id": "a", "type": "bash", "command": "echo"},
        {"id": "b", "type": "bash", "command": "echo", "depends_on": ["a"]},
        {"id": "c", "type": "bash", "command": "echo", "depends_on": ["a"]},
        {"id": "d", "type": "bash", "command": "echo", "depends_on": ["b", "c"]},
    ]))
    dag = DagGraph(spec)
    layers = dag.layers()
    layer_ids = [sorted(n.id for n in layer) for layer in layers if layer]
    assert layer_ids[0] == ["a"]
    assert sorted(layer_ids[1]) == ["b", "c"]
    assert layer_ids[2] == ["d"]
