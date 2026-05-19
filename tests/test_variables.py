# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
from __future__ import annotations

from dag_executor.variables import SubstitutionContext, substitute


def _ctx(**kw) -> SubstitutionContext:
    defaults = {
        "node_outputs": {},
        "workflow_id": "wf-123",
        "goal_text": "do the thing",
        "artifacts_dir": "/tmp/arts",
    }
    defaults.update(kw)
    return SubstitutionContext(**defaults)


def test_node_output_substitution():
    ctx = _ctx(node_outputs={"build": "dist/app.bin"})
    assert substitute("artifact: $build.output", ctx) == "artifact: dist/app.bin"


def test_workflow_id_substitution():
    ctx = _ctx()
    assert substitute("wf=$WORKFLOW_ID", ctx) == "wf=wf-123"


def test_goal_text_substitution():
    ctx = _ctx()
    assert substitute("goal: $GOAL_TEXT", ctx) == "goal: do the thing"


def test_artifacts_dir_substitution():
    ctx = _ctx()
    assert substitute("dir=$ARTIFACTS_DIR", ctx) == "dir=/tmp/arts"


def test_unknown_node_ref_passthrough():
    ctx = _ctx(node_outputs={})
    result = substitute("ref=$nonexistent.output end", ctx)
    assert result == "ref=$nonexistent.output end"


def test_multiple_substitutions_in_one_string():
    ctx = _ctx(node_outputs={"a": "hello", "b": "world"})
    result = substitute("$a.output $b.output", ctx)
    assert result == "hello world"


def test_no_substitution_needed():
    ctx = _ctx()
    assert substitute("plain text", ctx) == "plain text"
