# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import pytest

from dag_executor.models import NodeSpec, NodeType
from dag_executor.nodes.bash import BashNodeRunner
from dag_executor.variables import SubstitutionContext


def _ctx() -> SubstitutionContext:
    return SubstitutionContext(
        node_outputs={},
        workflow_id="wf",
        goal_text="goal",
        artifacts_dir="/tmp/a",
    )


def _node(cmd: str, timeout: int | None = None) -> NodeSpec:
    return NodeSpec(id="bash1", type=NodeType.BASH, command=cmd, timeout_seconds=timeout)


def test_success_exit_zero(tmp_path):
    runner = BashNodeRunner()
    result = runner.run(_node("true"), _ctx(), "/tmp/a", str(tmp_path))
    assert result.success is True
    assert result.exit_code == 0


def test_failure_nonzero_exit(tmp_path):
    runner = BashNodeRunner()
    result = runner.run(_node("false"), _ctx(), "/tmp/a", str(tmp_path))
    assert result.success is False
    assert result.exit_code != 0


def test_stdout_captured(tmp_path):
    runner = BashNodeRunner()
    result = runner.run(_node("echo hello_world"), _ctx(), "/tmp/a", str(tmp_path))
    assert "hello_world" in result.stdout


def test_stderr_captured_on_failure(tmp_path):
    runner = BashNodeRunner()
    result = runner.run(_node("sh -c 'echo err >&2; exit 1'"), _ctx(), "/tmp/a", str(tmp_path))
    assert result.success is False
    assert "err" in result.stderr


def test_variable_substituted_in_command(tmp_path):
    ctx = SubstitutionContext(
        node_outputs={"prev": "substituted_value"},
        workflow_id="wf",
        goal_text="goal",
        artifacts_dir="/tmp/a",
    )
    node = NodeSpec(id="b", type=NodeType.BASH, command="echo $prev.output")
    runner = BashNodeRunner()
    result = runner.run(node, ctx, "/tmp/a", str(tmp_path))
    assert "substituted_value" in result.stdout


def test_timeout_returns_failure(tmp_path):
    runner = BashNodeRunner()
    node = NodeSpec(id="slow", type=NodeType.BASH, command="sleep 10", timeout_seconds=1)
    result = runner.run(node, _ctx(), "/tmp/a", str(tmp_path))
    assert result.success is False
