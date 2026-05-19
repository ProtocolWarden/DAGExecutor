# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class SubstitutionContext:
    node_outputs: dict[str, str] = field(default_factory=dict)
    workflow_id: str = ""
    goal_text: str = ""
    artifacts_dir: str = ""


_BUILTIN = {
    "$WORKFLOW_ID": "workflow_id",
    "$GOAL_TEXT": "goal_text",
    "$ARTIFACTS_DIR": "artifacts_dir",
}

# Matches $nodeId.output — node ids are alphanumeric + underscores + hyphens
_NODE_OUTPUT_RE = re.compile(r"\$([A-Za-z0-9_\-]+)\.output")


def substitute(text: str, context: SubstitutionContext) -> str:
    for token, attr in _BUILTIN.items():
        text = text.replace(token, getattr(context, attr))

    def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
        node_id = m.group(1)
        if node_id in context.node_outputs:
            return context.node_outputs[node_id]
        return m.group(0)

    return _NODE_OUTPUT_RE.sub(_replace, text)
