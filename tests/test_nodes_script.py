# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

from dag_executor.models import NodeSpec, NodeType
from dag_executor.nodes.script import ScriptNodeRunner
from dag_executor.variables import SubstitutionContext


def _ctx() -> SubstitutionContext:
    return SubstitutionContext(
        node_outputs={},
        workflow_id="wf",
        goal_text="goal",
        artifacts_dir="/tmp/a",
    )


def test_python_script_runs(tmp_path):
    node = NodeSpec(id="s1", type=NodeType.SCRIPT, command='print("from_script")')
    runner = ScriptNodeRunner()
    result = runner.run(node, _ctx(), "/tmp/a", str(tmp_path))
    assert result.success is True
    assert "from_script" in result.stdout


def test_python_script_stdout_captured(tmp_path):
    node = NodeSpec(id="s2", type=NodeType.SCRIPT, command="x = 1 + 1\nprint(x)")
    runner = ScriptNodeRunner()
    result = runner.run(node, _ctx(), "/tmp/a", str(tmp_path))
    assert "2" in result.stdout


def test_python_script_failure(tmp_path):
    node = NodeSpec(id="s3", type=NodeType.SCRIPT, command="raise RuntimeError('boom')")
    runner = ScriptNodeRunner()
    result = runner.run(node, _ctx(), "/tmp/a", str(tmp_path))
    assert result.success is False
    assert result.exit_code != 0


def test_python_script_variable_substitution(tmp_path):
    ctx = SubstitutionContext(
        node_outputs={"prior": "hello_from_prior"},
        workflow_id="wf",
        goal_text="goal",
        artifacts_dir="/tmp/a",
    )
    node = NodeSpec(id="s4", type=NodeType.SCRIPT, command='print("$prior.output")')
    runner = ScriptNodeRunner()
    result = runner.run(node, ctx, "/tmp/a", str(tmp_path))
    assert "hello_from_prior" in result.stdout
