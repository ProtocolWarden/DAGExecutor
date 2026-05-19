# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from dag_executor.models import NodeResult, NodeSpec
from dag_executor.nodes.base import resolve_command, run_subprocess
from dag_executor.variables import SubstitutionContext, substitute


class LoopNodeRunner:
    """
    Two subtypes:
    - Static: run command up to max_iterations until stdout contains "DONE".
    - Dynamic fan-out: items_from resolves to a newline-separated list;
      command runs once per item concurrently with $ITEM in environment.
    """

    def run(
        self,
        node: NodeSpec,
        context: SubstitutionContext,
        artifacts_dir: str,
        working_directory: str,
    ) -> NodeResult:
        if node.items_from is not None:
            return self._fan_out(node, context, artifacts_dir, working_directory)
        return self._static_loop(node, context, working_directory)

    def _static_loop(
        self,
        node: NodeSpec,
        context: SubstitutionContext,
        working_directory: str,
    ) -> NodeResult:
        cmd = resolve_command(node, context)
        all_stdout: list[str] = []
        all_stderr: list[str] = []

        for _ in range(node.max_iterations):
            exit_code, stdout, stderr = run_subprocess(
                cmd, cwd=working_directory, timeout=node.timeout_seconds
            )
            all_stdout.append(stdout)
            all_stderr.append(stderr)
            if exit_code != 0:
                return NodeResult(
                    node_id=node.id,
                    success=False,
                    stdout="\n".join(all_stdout),
                    stderr="\n".join(all_stderr),
                    exit_code=exit_code,
                    error=stderr,
                )
            if "DONE" in stdout:
                break

        return NodeResult(
            node_id=node.id,
            success=True,
            stdout="\n".join(all_stdout),
            stderr="\n".join(all_stderr),
            exit_code=0,
        )

    def _fan_out(
        self,
        node: NodeSpec,
        context: SubstitutionContext,
        artifacts_dir: str,
        working_directory: str,
    ) -> NodeResult:
        items_raw = substitute(node.items_from or "", context)
        items = [line.strip() for line in items_raw.splitlines() if line.strip()]

        cmd_template = node.command or ""

        def run_item(item: str) -> tuple[str, int, str, str]:
            env = {**os.environ, "ITEM": item}
            item_context = SubstitutionContext(
                node_outputs={**context.node_outputs, "ITEM": item},
                workflow_id=context.workflow_id,
                goal_text=context.goal_text,
                artifacts_dir=context.artifacts_dir,
            )
            cmd = substitute(cmd_template, item_context)
            exit_code, stdout, stderr = run_subprocess(
                cmd, cwd=working_directory, env=env, timeout=node.timeout_seconds
            )
            return item, exit_code, stdout, stderr

        all_stdout: list[str] = []
        all_stderr: list[str] = []
        overall_success = True

        with ThreadPoolExecutor() as pool:
            futures = {pool.submit(run_item, item): item for item in items}
            for fut in as_completed(futures):
                item, exit_code, stdout, stderr = fut.result()
                all_stdout.append(f"[{item}] {stdout}")
                all_stderr.append(f"[{item}] {stderr}")
                if exit_code != 0:
                    overall_success = False

        return NodeResult(
            node_id=node.id,
            success=overall_success,
            stdout="\n".join(all_stdout),
            stderr="\n".join(all_stderr),
            exit_code=0 if overall_success else 1,
        )
