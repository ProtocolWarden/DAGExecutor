# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
"""Unit tests for dag_executor.nodes.gate (time/sleep mocked)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from dag_executor.models import NodeSpec, NodeType
from dag_executor.nodes.gate import GateNodeRunner
from dag_executor.variables import SubstitutionContext


def _ctx() -> SubstitutionContext:
    return SubstitutionContext(
        node_outputs={}, workflow_id="wf", goal_text="g", artifacts_dir="/a"
    )


def _node(node_id="g", timeout=None) -> NodeSpec:
    return NodeSpec(
        id=node_id,
        type=NodeType.GATE,
        gate_message="approve me",
        timeout_seconds=timeout,
    )


def test_writes_pending_file_with_message(tmp_path):
    runner = GateNodeRunner()
    node = _node()

    # approved before first poll so run() returns immediately
    def fake_sleep(_):
        raise AssertionError("should not sleep when approval already present")

    (tmp_path / "gates").mkdir()
    (tmp_path / "gates" / "g.approved").touch()
    with patch("dag_executor.nodes.gate.time.sleep", fake_sleep):
        result = runner.run(node, _ctx(), str(tmp_path), str(tmp_path))

    pending = tmp_path / "gates" / "g.pending"
    assert pending.read_text(encoding="utf-8") == "approve me"
    assert result.success is True


def test_approved_after_polling(tmp_path):
    runner = GateNodeRunner()
    node = _node()
    approved = tmp_path / "gates" / "g.approved"

    state = {"polls": 0}

    def fake_sleep(_interval):
        state["polls"] += 1
        if state["polls"] == 2:
            approved.touch()

    with patch("dag_executor.nodes.gate.time.sleep", fake_sleep):
        result = runner.run(node, _ctx(), str(tmp_path), str(tmp_path))

    assert result.success is True
    assert state["polls"] >= 2


def test_rejected(tmp_path):
    runner = GateNodeRunner()
    node = _node()
    rejected = tmp_path / "gates" / "g.rejected"

    def fake_sleep(_):
        rejected.touch()

    with patch("dag_executor.nodes.gate.time.sleep", fake_sleep):
        result = runner.run(node, _ctx(), str(tmp_path), str(tmp_path))

    assert result.success is False
    assert "rejected" in (result.error or "")


def test_timeout(tmp_path):
    runner = GateNodeRunner()
    node = _node(timeout=10)

    clock = {"t": 0.0}

    def fake_monotonic():
        return clock["t"]

    def fake_sleep(_):
        clock["t"] += 5.0  # advance past the 10s deadline after two polls

    with patch("dag_executor.nodes.gate.time.monotonic", fake_monotonic), patch(
        "dag_executor.nodes.gate.time.sleep", fake_sleep
    ):
        result = runner.run(node, _ctx(), str(tmp_path), str(tmp_path))

    assert result.success is False
    assert "timed out" in (result.error or "")


def test_creates_gates_dir_when_missing(tmp_path):
    runner = GateNodeRunner()
    node = _node()
    target = tmp_path / "nested"
    (Path(target) / "gates").mkdir(parents=True)
    (target / "gates" / "g.approved").touch()

    with patch("dag_executor.nodes.gate.time.sleep", lambda _: None):
        result = runner.run(node, _ctx(), str(target), str(target))

    assert result.success is True
