# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import shlex

from dag_executor.models import NodeResult, NodeSpec
from dag_executor.nodes.base import run_subprocess
from dag_executor.variables import SubstitutionContext, substitute


class AgentNodeRunner:
    """
    D1 invariant: goal_text from GraphSpec reaches `claude --message` verbatim.
    The node's command field (if present) is appended as an additional system prompt.
    """

    def run(
        self,
        node: NodeSpec,
        context: SubstitutionContext,
        artifacts_dir: str,
        working_directory: str,
    ) -> NodeResult:
        goal_text = context.goal_text
        model = node.model or "claude-sonnet-4-5"

        parts = [
            "claude",
            "--message", shlex.quote(goal_text),
            "--output-format", "json",
            "--no-auto-commits",
            "--model", shlex.quote(model),
        ]

        if node.command:
            extra = substitute(node.command, context)
            parts += ["--append-system-prompt", shlex.quote(extra)]

        cmd = " ".join(parts)
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
