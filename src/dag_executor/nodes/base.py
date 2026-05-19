# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import subprocess
from typing import Protocol

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
    cmd: str,
    *,
    shell: bool = True,
    cwd: str = ".",
    env: dict[str, str] | None = None,
    timeout: int | None = None,
) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timed out"


def resolve_command(node: NodeSpec, context: SubstitutionContext) -> str:
    if node.command is None:
        return ""
    return substitute(node.command, context)
