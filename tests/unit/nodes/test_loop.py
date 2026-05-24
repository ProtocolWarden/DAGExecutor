# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
"""Unit tests for dag_executor.nodes.loop."""
from __future__ import annotations

from unittest.mock import patch

from dag_executor.models import NodeSpec, NodeType
from dag_executor.nodes.loop import LoopNodeRunner
from dag_executor.variables import SubstitutionContext


def _ctx(outputs=None) -> SubstitutionContext:
    return SubstitutionContext(
        node_outputs=outputs or {},
        workflow_id="wf",
        goal_text="g",
        artifacts_dir="/a",
    )


def test_static_loop_stops_on_done():
    runner = LoopNodeRunner()
    calls = {"n": 0}

    def fake_run_subprocess(cmd, *, cwd=".", env=None, timeout=None):
        calls["n"] += 1
        # third iteration emits DONE
        out = "DONE" if calls["n"] == 3 else "still working"
        return 0, out, ""

    node = NodeSpec(id="lp", type=NodeType.LOOP, command="work.sh", max_iterations=10)
    with patch("dag_executor.nodes.loop.run_subprocess", fake_run_subprocess):
        result = runner.run(node, _ctx(), "/a", "/work")

    assert calls["n"] == 3
    assert result.success is True
    assert "DONE" in result.stdout


def test_static_loop_respects_max_iterations():
    runner = LoopNodeRunner()
    calls = {"n": 0}

    def fake_run_subprocess(cmd, *, cwd=".", env=None, timeout=None):
        calls["n"] += 1
        return 0, "never done", ""

    node = NodeSpec(id="lp", type=NodeType.LOOP, command="work.sh", max_iterations=4)
    with patch("dag_executor.nodes.loop.run_subprocess", fake_run_subprocess):
        result = runner.run(node, _ctx(), "/a", "/work")

    assert calls["n"] == 4
    assert result.success is True


def test_static_loop_fails_fast_on_nonzero_exit():
    runner = LoopNodeRunner()
    calls = {"n": 0}

    def fake_run_subprocess(cmd, *, cwd=".", env=None, timeout=None):
        calls["n"] += 1
        return 1, "out", "err"

    node = NodeSpec(id="lp", type=NodeType.LOOP, command="work.sh", max_iterations=5)
    with patch("dag_executor.nodes.loop.run_subprocess", fake_run_subprocess):
        result = runner.run(node, _ctx(), "/a", "/work")

    assert calls["n"] == 1  # stopped at first failure
    assert result.success is False
    assert result.exit_code == 1
    assert result.error == "err"


def test_fan_out_runs_command_per_item_with_item_env():
    runner = LoopNodeRunner()
    seen_items = []
    seen_envs = []

    def fake_run_subprocess(cmd, *, cwd=".", env=None, timeout=None):
        seen_items.append(cmd)
        seen_envs.append(env)
        return 0, f"processed {cmd}", ""

    node = NodeSpec(
        id="fan",
        type=NodeType.LOOP,
        command="handle $ITEM.output",
        items_from="alpha\nbeta\ngamma",
    )
    with patch("dag_executor.nodes.loop.run_subprocess", fake_run_subprocess):
        result = runner.run(node, _ctx(), "/a", "/work")

    # one invocation per non-empty item
    assert len(seen_items) == 3
    rendered = set(seen_items)
    assert {"handle alpha", "handle beta", "handle gamma"} == rendered
    # ITEM is injected into the child environment
    items_in_env = {e["ITEM"] for e in seen_envs}
    assert items_in_env == {"alpha", "beta", "gamma"}
    assert result.success is True


def test_fan_out_overall_failure_when_any_item_fails():
    runner = LoopNodeRunner()

    def fake_run_subprocess(cmd, *, cwd=".", env=None, timeout=None):
        # the 'bad' item fails
        code = 1 if env["ITEM"] == "bad" else 0
        return code, "", "fail" if code else ""

    node = NodeSpec(
        id="fan",
        type=NodeType.LOOP,
        command="run $ITEM.output",
        items_from="good\nbad",
    )
    with patch("dag_executor.nodes.loop.run_subprocess", fake_run_subprocess):
        result = runner.run(node, _ctx(), "/a", "/work")

    assert result.success is False
    assert result.exit_code == 1


def test_fan_out_ignores_blank_lines():
    runner = LoopNodeRunner()
    count = {"n": 0}

    def fake_run_subprocess(cmd, *, cwd=".", env=None, timeout=None):
        count["n"] += 1
        return 0, "", ""

    node = NodeSpec(
        id="fan", type=NodeType.LOOP, command="x", items_from="a\n\n  \nb\n"
    )
    with patch("dag_executor.nodes.loop.run_subprocess", fake_run_subprocess):
        runner.run(node, _ctx(), "/a", "/work")

    assert count["n"] == 2
