# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import os
import sys
import tempfile

from dag_executor.models import NodeResult, NodeSpec
from dag_executor.nodes.base import run_subprocess
from dag_executor.variables import SubstitutionContext, substitute


class ScriptNodeRunner:
    def run(
        self,
        node: NodeSpec,
        context: SubstitutionContext,
        artifacts_dir: str,
        working_directory: str,
    ) -> NodeResult:
        script_content = substitute(node.command or "", context)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, prefix=f"dag_{node.id}_"
        ) as f:
            f.write(script_content)
            script_path = f.name

        try:
            python = sys.executable
            exit_code, stdout, stderr = run_subprocess(
                f"{python} {script_path}",
                cwd=working_directory,
                timeout=node.timeout_seconds,
            )
        finally:
            try:
                os.unlink(script_path)
            except OSError:
                pass

        success = exit_code == 0
        return NodeResult(
            node_id=node.id,
            success=success,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            error=stderr if not success else None,
        )
