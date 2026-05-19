# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

from typing import Literal

from dag_executor.models import NodeResult, NodeSpec
from dag_executor.nodes.base import run_subprocess
from dag_executor.variables import SubstitutionContext, substitute


class AgentNodeRunner:
    """
    D1 invariant: goal_text from GraphSpec reaches the CLI verbatim.
    Supports claude_code (default) and codex_cli worker backends.
    """

    def run(
        self,
        node: NodeSpec,
        context: SubstitutionContext,
        artifacts_dir: str,
        working_directory: str,
        worker_backend: Literal["claude_code", "codex_cli"] = "claude_code",
    ) -> NodeResult:
        goal_text = context.goal_text
        model = node.model or "claude-sonnet-4-5"

        if worker_backend == "codex_cli":
            cmd = self._build_codex_cmd(goal_text, model)
        else:
            cmd = self._build_claude_cmd(goal_text, model, node, context)

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

    def _build_claude_cmd(
        self,
        goal_text: str,
        model: str,
        node: NodeSpec,
        context: SubstitutionContext,
    ) -> list[str]:
        cmd = [
            "claude",
            "--message", goal_text,
            "--output-format", "json",
            "--no-auto-commits",
            "--model", model,
        ]
        if node.command:
            extra = substitute(node.command, context)
            cmd += ["--append-system-prompt", extra]
        return cmd

    def _build_codex_cmd(self, goal_text: str, model: str) -> list[str]:
        return ["codex", "--model", model, "--approval-mode", "full-auto", "-q", goal_text]
