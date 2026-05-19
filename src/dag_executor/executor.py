# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any

from dag_executor.evidence import aggregate_evidence
from dag_executor.graph import DagGraph
from dag_executor.loader import load_graph_file
from dag_executor.models import GraphSpec, NodeResult, NodeSpec, NodeType, TriggerRule
from dag_executor.nodes.agent import AgentNodeRunner
from dag_executor.nodes.bash import BashNodeRunner
from dag_executor.nodes.gate import GateNodeRunner
from dag_executor.nodes.loop import LoopNodeRunner
from dag_executor.nodes.script import ScriptNodeRunner
from dag_executor.variables import SubstitutionContext


_RUNNERS = {
    NodeType.AGENT: AgentNodeRunner,
    NodeType.BASH: BashNodeRunner,
    NodeType.SCRIPT: ScriptNodeRunner,
    NodeType.LOOP: LoopNodeRunner,
    NodeType.GATE: GateNodeRunner,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _should_run(node: NodeSpec, completed: dict[str, NodeResult]) -> bool:
    if not node.depends_on:
        return True

    dep_results = [completed[dep] for dep in node.depends_on if dep in completed]

    if node.trigger_rule == TriggerRule.ALL_SUCCESS:
        return all(r.success for r in dep_results)
    if node.trigger_rule == TriggerRule.ALL_DONE:
        return True
    if node.trigger_rule == TriggerRule.ANY_SUCCESS:
        return any(r.success for r in dep_results)
    return True


def _build_context(
    spec: GraphSpec,
    completed: dict[str, NodeResult],
    artifacts_dir: str,
) -> SubstitutionContext:
    return SubstitutionContext(
        node_outputs={nid: r.stdout for nid, r in completed.items()},
        workflow_id=spec.workflow_id,
        goal_text=spec.goal_text,
        artifacts_dir=artifacts_dir,
    )


class DagExecutorRunner:
    def __init__(
        self,
        artifacts_dir: str | None = None,
        working_directory: str = ".",
        timeout_seconds: int | None = None,
    ) -> None:
        self._artifacts_dir = artifacts_dir
        self._working_directory = working_directory
        self._timeout_seconds = timeout_seconds

    def run_graph(self, spec: GraphSpec) -> dict[str, Any]:
        started_at = _now()
        artifacts_dir = self._artifacts_dir or tempfile.mkdtemp(prefix="dag_artifacts_")
        os.makedirs(artifacts_dir, exist_ok=True)

        dag = DagGraph(spec)
        layers = dag.layers()

        completed: dict[str, NodeResult] = {}
        all_results: list[NodeResult] = []

        for layer in layers:
            layer_results = self._run_layer(
                layer, spec, completed, artifacts_dir
            )
            for result in layer_results:
                completed[result.node_id] = result
                all_results.append(result)

        evidence = aggregate_evidence(all_results)
        overall_success = all(r.success for r in all_results)

        finished_at = _now()

        # Return a plain dict compatible with RuntimeResult fields.
        # Callers that have rxp installed can hydrate a RuntimeResult from this.
        return {
            "schema_version": "0.1",
            "contract_kind": "runtime_result",
            "invocation_id": spec.workflow_id,
            "runtime_name": "dag-executor",
            "runtime_kind": "subprocess",
            "status": "succeeded" if overall_success else "failed",
            "exit_code": 0 if overall_success else 1,
            "started_at": started_at,
            "finished_at": finished_at,
            "stdout_path": None,
            "stderr_path": None,
            "artifacts": [],
            "error_summary": None if overall_success else self._error_summary(all_results),
            "metadata": {
                "evidence": evidence,
                "node_results": [
                    {
                        "node_id": r.node_id,
                        "success": r.success,
                        "exit_code": r.exit_code,
                        "error": r.error,
                    }
                    for r in all_results
                ],
            },
        }

    def _run_layer(
        self,
        layer: list[NodeSpec],
        spec: GraphSpec,
        completed: dict[str, NodeResult],
        artifacts_dir: str,
    ) -> list[NodeResult]:
        results: list[NodeResult] = []

        def run_node(node: NodeSpec) -> NodeResult:
            ctx = _build_context(spec, completed, artifacts_dir)
            if not _should_run(node, completed):
                return NodeResult(
                    node_id=node.id,
                    success=False,
                    error=f"Skipped: upstream dependency failed (trigger_rule={node.trigger_rule})",
                )
            runner_cls = _RUNNERS[node.type]
            runner = runner_cls()
            return runner.run(
                node,
                ctx,
                artifacts_dir=artifacts_dir,
                working_directory=self._working_directory,
            )

        if len(layer) == 1:
            results.append(run_node(layer[0]))
        else:
            with ThreadPoolExecutor() as pool:
                futures = {pool.submit(run_node, node): node for node in layer}
                for fut in as_completed(futures):
                    results.append(fut.result())

        return results

    def run_from_yaml(
        self,
        yaml_path: str,
        goal_text: str = "",
        variables: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        spec = load_graph_file(yaml_path, goal_text=goal_text)
        if variables:
            spec.variables.update(variables)
        return self.run_graph(spec)

    @staticmethod
    def _error_summary(results: list[NodeResult]) -> str:
        failed = [r for r in results if not r.success]
        parts = [f"{r.node_id}: {r.error or 'failed'}" for r in failed]
        return "; ".join(parts)
