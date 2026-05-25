# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    AGENT = "agent"
    BASH = "bash"
    SCRIPT = "script"
    LOOP = "loop"
    GATE = "gate"


class TriggerRule(str, Enum):
    ALL_SUCCESS = "all_success"
    ALL_DONE = "all_done"
    ANY_SUCCESS = "any_success"


@dataclass
class NodeSpec:
    id: str
    type: NodeType
    depends_on: list[str] = field(default_factory=list)
    # agent / bash / script
    command: str | None = None
    model: str | None = None
    effort: str | None = None
    backend_models: dict[str, str] = field(default_factory=dict)
    backend_efforts: dict[str, str] = field(default_factory=dict)
    context: list[str] = field(default_factory=list)
    # loop
    items_from: str | None = None
    max_iterations: int = 10
    # gate
    gate_message: str | None = None
    # common
    trigger_rule: TriggerRule = TriggerRule.ALL_SUCCESS
    timeout_seconds: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def model_for_backend(self, backend: str, default_model: str) -> str:
        return self.backend_models.get(backend, self.model or default_model)

    def effort_for_backend(self, backend: str) -> str | None:
        return self.backend_efforts.get(backend, self.effort)


@dataclass
class GraphSpec:
    workflow_id: str
    nodes: list[NodeSpec]
    variables: dict[str, str] = field(default_factory=dict)
    goal_text: str = ""


@dataclass
class NodeResult:
    node_id: str
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    artifacts: list[str] = field(default_factory=list)
    error: str | None = None
