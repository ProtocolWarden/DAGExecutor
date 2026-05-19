# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import rustworkx as rx

from dag_executor.models import GraphSpec, NodeSpec


class CyclicGraphError(Exception):
    pass


class DagGraph:
    def __init__(self, spec: GraphSpec) -> None:
        self._spec = spec
        self._graph: rx.PyDiGraph = rx.PyDiGraph()
        # node_id → rustworkx index
        self._index_map: dict[str, int] = {}

        for node in spec.nodes:
            idx = self._graph.add_node(node)
            self._index_map[node.id] = idx

        for node in spec.nodes:
            for dep_id in node.depends_on:
                dep_idx = self._index_map[dep_id]
                node_idx = self._index_map[node.id]
                # edge: dep → node (dep must finish before node starts)
                self._graph.add_edge(dep_idx, node_idx, None)

        if not rx.is_directed_acyclic_graph(self._graph):
            raise CyclicGraphError(
                f"Cycle detected in workflow {spec.workflow_id!r}"
            )

    def layers(self) -> list[list[NodeSpec]]:
        # rx.layers needs root nodes (nodes with no predecessors) as first_layer
        roots = [
            idx for idx in self._graph.node_indices()
            if len(self._graph.predecessors(idx)) == 0
        ]
        if not roots:
            return []
        # rx.layers returns list of lists of node data (not indices)
        raw_layers = rx.layers(self._graph, roots)
        return [list(layer) for layer in raw_layers]

    def get_node(self, node_id: str) -> NodeSpec:
        idx = self._index_map[node_id]
        return self._graph[idx]
