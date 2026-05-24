# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
"""Unit tests for dag_executor.models."""
from __future__ import annotations

from dag_executor.models import (
    GraphSpec,
    NodeResult,
    NodeSpec,
    NodeType,
    TriggerRule,
)


def test_node_type_values():
    assert NodeType.AGENT.value == "agent"
    assert NodeType("bash") is NodeType.BASH
    assert {t.value for t in NodeType} == {
        "agent",
        "bash",
        "script",
        "loop",
        "gate",
    }


def test_trigger_rule_default_and_values():
    assert TriggerRule("all_done") is TriggerRule.ALL_DONE
    assert {t.value for t in TriggerRule} == {
        "all_success",
        "all_done",
        "any_success",
    }


def test_node_spec_defaults():
    node = NodeSpec(id="n", type=NodeType.BASH)
    assert node.depends_on == []
    assert node.command is None
    assert node.max_iterations == 10
    assert node.trigger_rule is TriggerRule.ALL_SUCCESS
    assert node.metadata == {}


def test_node_spec_default_factories_are_independent():
    a = NodeSpec(id="a", type=NodeType.BASH)
    b = NodeSpec(id="b", type=NodeType.BASH)
    a.depends_on.append("x")
    a.metadata["k"] = "v"
    assert b.depends_on == []
    assert b.metadata == {}


def test_graph_spec_defaults():
    spec = GraphSpec(workflow_id="wf", nodes=[])
    assert spec.variables == {}
    assert spec.goal_text == ""


def test_node_result_defaults():
    r = NodeResult(node_id="n", success=True)
    assert r.stdout == ""
    assert r.stderr == ""
    assert r.exit_code is None
    assert r.artifacts == []
    assert r.error is None


def test_node_type_is_str_enum():
    # str-Enum: members compare equal to their string value
    assert NodeType.GATE == "gate"
