# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

from dag_executor.evidence import aggregate_evidence
from dag_executor.models import NodeResult


def test_all_success():
    results = [
        NodeResult(node_id="a", success=True),
        NodeResult(node_id="b", success=True),
    ]
    ev = aggregate_evidence(results)
    assert ev["nodes_run"] == 2
    assert ev["nodes_succeeded"] == 2
    assert ev["nodes_failed"] == 0
    assert ev["failed_nodes"] == []


def test_mixed_results():
    results = [
        NodeResult(node_id="a", success=True),
        NodeResult(node_id="b", success=False),
    ]
    ev = aggregate_evidence(results)
    assert ev["nodes_succeeded"] == 1
    assert ev["nodes_failed"] == 1
    assert ev["failed_nodes"] == ["b"]


def test_no_artifacts():
    results = [NodeResult(node_id="x", success=True)]
    ev = aggregate_evidence(results)
    assert ev["artifacts"] == []


def test_artifacts_aggregated():
    results = [
        NodeResult(node_id="a", success=True, artifacts=["file1.txt", "file2.txt"]),
        NodeResult(node_id="b", success=True, artifacts=["file3.txt"]),
    ]
    ev = aggregate_evidence(results)
    assert sorted(ev["artifacts"]) == ["file1.txt", "file2.txt", "file3.txt"]
