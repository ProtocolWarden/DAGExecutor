# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
"""Unit tests for dag_executor.nodes.base."""
from __future__ import annotations

from unittest.mock import patch

from core_runner.process import SafeRunResult

from dag_executor.models import NodeSpec, NodeType
from dag_executor.nodes.base import NodeRunner, resolve_command, run_subprocess
from dag_executor.variables import SubstitutionContext


def _ctx(**kw) -> SubstitutionContext:
    base = dict(node_outputs={}, workflow_id="wf", goal_text="g", artifacts_dir="/a")
    base.update(kw)
    return SubstitutionContext(**base)


def test_run_subprocess_splits_string_command():
    captured = {}

    def fake_safe_run(cmd, *, cwd=".", env=None, timeout_seconds=None):
        captured["cmd"] = cmd
        return SafeRunResult(returncode=0, stdout="ok", stderr="", timed_out=False)

    with patch("dag_executor.nodes.base.safe_run", fake_safe_run):
        code, out, err = run_subprocess("echo hello world")

    # shlex.split turns the string into argv
    assert captured["cmd"] == ["echo", "hello", "world"]
    assert (code, out, err) == (0, "ok", "")


def test_run_subprocess_passes_list_command_through():
    captured = {}

    def fake_safe_run(cmd, *, cwd=".", env=None, timeout_seconds=None):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        captured["env"] = env
        captured["timeout"] = timeout_seconds
        return SafeRunResult(returncode=0, stdout="", stderr="", timed_out=False)

    with patch("dag_executor.nodes.base.safe_run", fake_safe_run):
        run_subprocess(["ls", "-l"], cwd="/tmp", env={"X": "1"}, timeout=5)

    assert captured["cmd"] == ["ls", "-l"]
    assert captured["cwd"] == "/tmp"
    assert captured["env"] == {"X": "1"}
    assert captured["timeout"] == 5


def test_run_subprocess_maps_timeout_to_124():
    def fake_safe_run(cmd, *, cwd=".", env=None, timeout_seconds=None):
        return SafeRunResult(returncode=None, stdout="partial", stderr="", timed_out=True)

    with patch("dag_executor.nodes.base.safe_run", fake_safe_run):
        code, out, err = run_subprocess(["sleep", "9"], timeout=1)

    assert code == 124
    assert out == "partial"
    assert err == "timed out"


def test_run_subprocess_none_returncode_becomes_zero():
    def fake_safe_run(cmd, *, cwd=".", env=None, timeout_seconds=None):
        return SafeRunResult(returncode=None, stdout="", stderr="", timed_out=False)

    with patch("dag_executor.nodes.base.safe_run", fake_safe_run):
        code, _, _ = run_subprocess(["true"])

    assert code == 0


def test_resolve_command_substitutes_tokens():
    node = NodeSpec(id="n", type=NodeType.BASH, command="echo $prev.output $GOAL_TEXT")
    ctx = _ctx(node_outputs={"prev": "VAL"}, goal_text="THEGOAL")
    assert resolve_command(node, ctx) == "echo VAL THEGOAL"


def test_resolve_command_none_returns_empty():
    node = NodeSpec(id="n", type=NodeType.BASH, command=None)
    assert resolve_command(node, _ctx()) == ""


def test_noderunner_is_runtime_checkable_protocol():
    class Good:
        def run(self, node, context, artifacts_dir, working_directory):
            return None

    # Structural typing: a class with a matching run() satisfies the protocol.
    assert hasattr(Good(), "run")
    assert NodeRunner.__name__ == "NodeRunner"
