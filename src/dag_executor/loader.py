# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from dag_executor.models import GraphSpec, NodeSpec, NodeType, TriggerRule


class LoaderError(Exception):
    pass


def _parse_node(raw: dict[str, Any]) -> NodeSpec:
    node_id = raw.get("id")
    if not node_id:
        raise LoaderError("Node missing required field: id")

    raw_type = raw.get("type")
    try:
        node_type = NodeType(raw_type)
    except ValueError:
        raise LoaderError(f"Unknown node type {raw_type!r} on node {node_id!r}")

    raw_trigger = raw.get("trigger_rule", TriggerRule.ALL_SUCCESS.value)
    try:
        trigger_rule = TriggerRule(raw_trigger)
    except ValueError:
        raise LoaderError(f"Unknown trigger_rule {raw_trigger!r} on node {node_id!r}")

    return NodeSpec(
        id=node_id,
        type=node_type,
        depends_on=raw.get("depends_on", []),
        command=raw.get("command"),
        model=raw.get("model"),
        context=raw.get("context", []),
        items_from=raw.get("items_from"),
        max_iterations=int(raw.get("max_iterations", 10)),
        gate_message=raw.get("gate_message"),
        trigger_rule=trigger_rule,
        timeout_seconds=raw.get("timeout_seconds"),
        metadata=raw.get("metadata", {}),
    )


def _validate(spec: GraphSpec) -> None:
    seen_ids: set[str] = set()
    for node in spec.nodes:
        if node.id in seen_ids:
            raise LoaderError(f"Duplicate node id: {node.id!r}")
        seen_ids.add(node.id)

    for node in spec.nodes:
        for dep in node.depends_on:
            if dep not in seen_ids:
                raise LoaderError(
                    f"Node {node.id!r} depends on unknown node {dep!r}"
                )
        if node.type == NodeType.GATE and not node.gate_message:
            raise LoaderError(f"Gate node {node.id!r} missing gate_message")
        if node.type == NodeType.LOOP and node.command is None and node.items_from is None:
            raise LoaderError(
                f"Loop node {node.id!r} must have either command or items_from"
            )


def load_graph(data: dict[str, Any], goal_text: str = "") -> GraphSpec:
    workflow_id = data.get("workflow_id", "")
    if not workflow_id:
        raise LoaderError("Graph missing required field: workflow_id")

    raw_nodes = data.get("nodes", [])
    nodes = [_parse_node(n) for n in raw_nodes]

    spec = GraphSpec(
        workflow_id=workflow_id,
        nodes=nodes,
        variables=data.get("variables", {}),
        goal_text=goal_text,
    )
    _validate(spec)
    return spec


def load_graph_file(path: str, goal_text: str = "") -> GraphSpec:
    text = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(text) or {}
    return load_graph(data, goal_text=goal_text)
