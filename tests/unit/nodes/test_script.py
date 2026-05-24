# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
"""Unit tests for dag_executor.nodes.script (subprocess mocked)."""
from __future__ import annotations

import os
import sys
from unittest.mock import patch

from dag_executor.models import NodeSpec, NodeType
from dag_executor.nodes.script import ScriptNodeRunner
from dag_executor.variables import SubstitutionContext


def _ctx(outputs=None) -> SubstitutionContext:
    return SubstitutionContext(
        node_outputs=outputs or {}, workflow_id="wf", goal_text="g", artifacts_dir="/a"
    )


def test_writes_substituted_script_to_tempfile_and_runs_with_python():
    runner = ScriptNodeRunner()
    captured = {}

    def fake_run_subprocess(cmd, *, cwd=".", timeout=None):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        # the script path is the temp file the runner just wrote
        with open(cmd[1], encoding="utf-8") as fh:
            captured["script"] = fh.read()
        return 0, "ran", ""

    node = NodeSpec(
        id="s", type=NodeType.SCRIPT, command='print("$prior.output")', timeout_seconds=4
    )
    with patch("dag_executor.nodes.script.run_subprocess", fake_run_subprocess):
        result = runner.run(node, _ctx({"prior": "HELLO"}), "/a", "/work")

    assert captured["cmd"][0] == sys.executable
    assert captured["script"] == 'print("HELLO")'  # variable substituted
    assert captured["cwd"] == "/work"
    assert result.success is True
    assert result.stdout == "ran"


def test_tempfile_is_removed_after_run():
    runner = ScriptNodeRunner()
    paths = {}

    def fake_run_subprocess(cmd, *, cwd=".", timeout=None):
        paths["script"] = cmd[1]
        assert os.path.exists(cmd[1])  # exists during run
        return 0, "", ""

    node = NodeSpec(id="s", type=NodeType.SCRIPT, command="print(1)")
    with patch("dag_executor.nodes.script.run_subprocess", fake_run_subprocess):
        runner.run(node, _ctx(), "/a", "/work")

    assert not os.path.exists(paths["script"])  # cleaned up afterwards


def test_tempfile_removed_even_when_subprocess_raises():
    runner = ScriptNodeRunner()
    paths = {}

    def fake_run_subprocess(cmd, *, cwd=".", timeout=None):
        paths["script"] = cmd[1]
        raise RuntimeError("subprocess blew up")

    node = NodeSpec(id="s", type=NodeType.SCRIPT, command="print(1)")
    with patch("dag_executor.nodes.script.run_subprocess", fake_run_subprocess):
        try:
            runner.run(node, _ctx(), "/a", "/work")
        except RuntimeError:
            pass

    assert not os.path.exists(paths["script"])


def test_nonzero_exit_marks_failure():
    runner = ScriptNodeRunner()

    def fake_run_subprocess(cmd, *, cwd=".", timeout=None):
        return 1, "", "traceback"

    node = NodeSpec(id="s", type=NodeType.SCRIPT, command="raise SystemExit(1)")
    with patch("dag_executor.nodes.script.run_subprocess", fake_run_subprocess):
        result = runner.run(node, _ctx(), "/a", "/work")

    assert result.success is False
    assert result.exit_code == 1
    assert result.error == "traceback"


def test_none_command_writes_empty_script():
    runner = ScriptNodeRunner()
    captured = {}

    def fake_run_subprocess(cmd, *, cwd=".", timeout=None):
        with open(cmd[1], encoding="utf-8") as fh:
            captured["script"] = fh.read()
        return 0, "", ""

    node = NodeSpec(id="s", type=NodeType.SCRIPT, command=None)
    with patch("dag_executor.nodes.script.run_subprocess", fake_run_subprocess):
        runner.run(node, _ctx(), "/a", "/work")

    assert captured["script"] == ""
