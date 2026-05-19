# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from dag_executor.models import NodeSpec, NodeType
from dag_executor.nodes.gate import GateNodeRunner, _POLL_INTERVAL
from dag_executor.variables import SubstitutionContext


def _ctx() -> SubstitutionContext:
    return SubstitutionContext(
        node_outputs={},
        workflow_id="wf",
        goal_text="goal",
        artifacts_dir="/tmp/a",
    )


def _gate_node(node_id: str = "approval", timeout: int | None = None) -> NodeSpec:
    return NodeSpec(
        id=node_id,
        type=NodeType.GATE,
        gate_message="Please review and approve",
        timeout_seconds=timeout,
    )


def test_gate_approved_path(tmp_path):
    node = _gate_node()
    runner = GateNodeRunner()
    artifacts_dir = str(tmp_path)

    def approve():
        time.sleep(_POLL_INTERVAL + 0.1)
        (tmp_path / "gates" / f"{node.id}.approved").touch()

    t = threading.Thread(target=approve, daemon=True)
    t.start()
    result = runner.run(node, _ctx(), artifacts_dir, str(tmp_path))
    t.join(timeout=5)
    assert result.success is True


def test_gate_rejected_path(tmp_path):
    node = _gate_node()
    runner = GateNodeRunner()
    artifacts_dir = str(tmp_path)

    def reject():
        time.sleep(_POLL_INTERVAL + 0.1)
        (tmp_path / "gates" / f"{node.id}.rejected").touch()

    t = threading.Thread(target=reject, daemon=True)
    t.start()
    result = runner.run(node, _ctx(), artifacts_dir, str(tmp_path))
    t.join(timeout=5)
    assert result.success is False
    assert "rejected" in (result.error or "")


def test_gate_timeout_path(tmp_path):
    node = _gate_node(timeout=1)
    runner = GateNodeRunner()
    result = runner.run(node, _ctx(), str(tmp_path), str(tmp_path))
    assert result.success is False
    assert "timed out" in (result.error or "")


def test_gate_pending_file_created(tmp_path):
    node = _gate_node(timeout=1)
    runner = GateNodeRunner()
    runner.run(node, _ctx(), str(tmp_path), str(tmp_path))
    pending = tmp_path / "gates" / f"{node.id}.pending"
    assert pending.exists()
    assert pending.read_text() == "Please review and approve"
