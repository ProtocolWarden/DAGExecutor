# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

from typing import Any

from dag_executor.models import NodeResult


def aggregate_evidence(node_results: list[NodeResult]) -> dict[str, Any]:
    return {
        "nodes_run": len(node_results),
        "nodes_succeeded": sum(1 for r in node_results if r.success),
        "nodes_failed": sum(1 for r in node_results if not r.success),
        "artifacts": [a for r in node_results for a in r.artifacts],
        "failed_nodes": [r.node_id for r in node_results if not r.success],
    }
