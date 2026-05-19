# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import shlex
from typing import Protocol

from core_runner.process import safe_run

from dag_executor.models import NodeResult, NodeSpec
from dag_executor.variables import SubstitutionContext, substitute


class NodeRunner(Protocol):
    def run(
        self,
        node: NodeSpec,
        context: SubstitutionContext,
        artifacts_dir: str,
        working_directory: str,
    ) -> NodeResult: ...


def run_subprocess(
    cmd: list[str] | str,
    *,
    cwd: str = ".",
    env: dict[str, str] | None = None,
    timeout: int | None = None,
) -> tuple[int, str, str]:
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    result = safe_run(cmd, cwd=cwd, env=env, timeout_seconds=timeout)
    if result.timed_out:
        return 124, result.stdout, "timed out"
    return result.returncode or 0, result.stdout, result.stderr


def resolve_command(node: NodeSpec, context: SubstitutionContext) -> str:
    if node.command is None:
        return ""
    return substitute(node.command, context)
