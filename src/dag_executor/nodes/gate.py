# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import time
from pathlib import Path

from dag_executor.models import NodeResult, NodeSpec
from dag_executor.variables import SubstitutionContext


_POLL_INTERVAL = 2.0


class GateNodeRunner:
    def run(
        self,
        node: NodeSpec,
        context: SubstitutionContext,
        artifacts_dir: str,
        working_directory: str,
    ) -> NodeResult:
        gates_dir = Path(artifacts_dir) / "gates"
        gates_dir.mkdir(parents=True, exist_ok=True)

        pending_path = gates_dir / f"{node.id}.pending"
        approved_path = gates_dir / f"{node.id}.approved"
        rejected_path = gates_dir / f"{node.id}.rejected"

        pending_path.write_text(node.gate_message or "")

        deadline = (
            time.monotonic() + node.timeout_seconds
            if node.timeout_seconds is not None
            else None
        )

        while True:
            if approved_path.exists():
                return NodeResult(node_id=node.id, success=True)
            if rejected_path.exists():
                return NodeResult(
                    node_id=node.id,
                    success=False,
                    error=f"Gate {node.id!r} rejected",
                )
            if deadline is not None and time.monotonic() >= deadline:
                return NodeResult(
                    node_id=node.id,
                    success=False,
                    error=f"Gate {node.id!r} timed out after {node.timeout_seconds}s",
                )
            time.sleep(_POLL_INTERVAL)
