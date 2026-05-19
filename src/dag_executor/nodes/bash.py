# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

from dag_executor.models import NodeResult, NodeSpec
from dag_executor.nodes.base import resolve_command, run_subprocess
from dag_executor.variables import SubstitutionContext


class BashNodeRunner:
    def run(
        self,
        node: NodeSpec,
        context: SubstitutionContext,
        artifacts_dir: str,
        working_directory: str,
    ) -> NodeResult:
        cmd = resolve_command(node, context)
        exit_code, stdout, stderr = run_subprocess(
            cmd,
            cwd=working_directory,
            timeout=node.timeout_seconds,
        )
        success = exit_code == 0
        return NodeResult(
            node_id=node.id,
            success=success,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            error=stderr if not success else None,
        )
