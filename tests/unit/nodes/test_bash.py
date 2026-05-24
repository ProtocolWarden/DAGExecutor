# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
"""Unit tests for dag_executor.nodes.bash (subprocess mocked)."""
from __future__ import annotations

from unittest.mock import patch

from dag_executor.models import NodeSpec, NodeType
from dag_executor.nodes.bash import BashNodeRunner
from dag_executor.variables import SubstitutionContext


def _ctx(outputs=None) -> SubstitutionContext:
    return SubstitutionContext(
        node_outputs=outputs or {},
        workflow_id="wf",
        goal_text="g",
        artifacts_dir="/a",
    )


def test_resolved_command_is_passed_to_subprocess():
    runner = BashNodeRunner()
    captured = {}

    def fake_run_subprocess(cmd, *, cwd=".", timeout=None):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        captured["timeout"] = timeout
        return 0, "hi", ""

    node = NodeSpec(
        id="b", type=NodeType.BASH, command="echo $prev.output", timeout_seconds=7
    )
    with patch("dag_executor.nodes.bash.run_subprocess", fake_run_subprocess):
        result = runner.run(node, _ctx({"prev": "VAL"}), "/a", "/work")

    assert captured["cmd"] == "echo VAL"  # variable substituted
    assert captured["cwd"] == "/work"
    assert captured["timeout"] == 7
    assert result.success is True
    assert result.stdout == "hi"


def test_nonzero_exit_marks_failure_and_error():
    runner = BashNodeRunner()

    def fake_run_subprocess(cmd, *, cwd=".", timeout=None):
        return 3, "", "kaboom"

    node = NodeSpec(id="b", type=NodeType.BASH, command="false")
    with patch("dag_executor.nodes.bash.run_subprocess", fake_run_subprocess):
        result = runner.run(node, _ctx(), "/a", "/work")

    assert result.success is False
    assert result.exit_code == 3
    assert result.error == "kaboom"


def test_node_id_preserved_in_result():
    runner = BashNodeRunner()

    def fake_run_subprocess(cmd, *, cwd=".", timeout=None):
        return 0, "", ""

    node = NodeSpec(id="my-node", type=NodeType.BASH, command="true")
    with patch("dag_executor.nodes.bash.run_subprocess", fake_run_subprocess):
        result = runner.run(node, _ctx(), "/a", "/work")

    assert result.node_id == "my-node"
    assert result.error is None
