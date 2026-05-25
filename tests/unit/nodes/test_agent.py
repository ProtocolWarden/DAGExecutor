# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
"""Unit tests for dag_executor.nodes.agent."""
from __future__ import annotations

from unittest.mock import patch

from dag_executor.models import NodeSpec, NodeType
from dag_executor.nodes.agent import AgentNodeRunner
from dag_executor.variables import SubstitutionContext


def _ctx(goal: str = "build the thing", outputs=None) -> SubstitutionContext:
    return SubstitutionContext(
        node_outputs=outputs or {},
        workflow_id="wf",
        goal_text=goal,
        artifacts_dir="/a",
    )


def _node(**kw) -> NodeSpec:
    base = dict(id="agent1", type=NodeType.AGENT)
    base.update(kw)
    return NodeSpec(**base)


def test_claude_cmd_carries_goal_text_verbatim():
    runner = AgentNodeRunner()
    cmd = runner._build_claude_cmd("exact goal", "model-x", "medium", _node(), _ctx())
    # D1 invariant: goal_text reaches --message verbatim.
    assert "--message" in cmd
    assert cmd[cmd.index("--message") + 1] == "exact goal"
    assert "--model" in cmd and cmd[cmd.index("--model") + 1] == "model-x"
    assert "--effort" in cmd and cmd[cmd.index("--effort") + 1] == "medium"


def test_claude_cmd_appends_system_prompt_when_command_present():
    runner = AgentNodeRunner()
    node = _node(command="context for $GOAL_TEXT")
    ctx = _ctx(goal="G")
    cmd = runner._build_claude_cmd("G", "m", None, node, ctx)
    assert "--append-system-prompt" in cmd
    assert cmd[cmd.index("--append-system-prompt") + 1] == "context for G"


def test_claude_cmd_omits_system_prompt_when_no_command():
    runner = AgentNodeRunner()
    cmd = runner._build_claude_cmd("G", "m", None, _node(), _ctx())
    assert "--append-system-prompt" not in cmd


def test_codex_cmd_structure():
    runner = AgentNodeRunner()
    cmd = runner._build_codex_cmd("do it", "gpt-x", "low")
    assert cmd[0] == "codex"
    assert cmd[-1] == "do it"
    assert "--model" in cmd and cmd[cmd.index("--model") + 1] == "gpt-x"
    assert 'model_reasoning_effort="low"' in cmd


def test_run_uses_default_model_and_claude_backend():
    runner = AgentNodeRunner()
    captured = {}

    def fake_run_subprocess(cmd, *, cwd=".", timeout=None):
        captured["cmd"] = cmd
        return 0, "agent stdout", ""

    with patch("dag_executor.nodes.agent.run_subprocess", fake_run_subprocess):
        result = runner.run(_node(), _ctx(goal="goalz"), "/a", "/work")

    assert captured["cmd"][0] == "claude"
    assert "claude-sonnet-4-5" in captured["cmd"]  # default model
    assert result.success is True
    assert result.stdout == "agent stdout"
    assert result.error is None


def test_run_codex_backend_selected():
    runner = AgentNodeRunner()
    captured = {}

    def fake_run_subprocess(cmd, *, cwd=".", timeout=None):
        captured["cmd"] = cmd
        return 0, "", ""

    with patch("dag_executor.nodes.agent.run_subprocess", fake_run_subprocess):
        runner.run(
            _node(
                backend_models={"codex_cli": "gpt-5.4"},
                backend_efforts={"codex_cli": "medium"},
            ),
            _ctx(),
            "/a",
            "/work",
            worker_backend="codex_cli",
        )

    assert captured["cmd"][0] == "codex"
    assert "gpt-5.4" in captured["cmd"]
    assert 'model_reasoning_effort="medium"' in captured["cmd"]


def test_run_failure_sets_error_from_stderr():
    runner = AgentNodeRunner()

    def fake_run_subprocess(cmd, *, cwd=".", timeout=None):
        return 2, "", "boom"

    with patch("dag_executor.nodes.agent.run_subprocess", fake_run_subprocess):
        result = runner.run(_node(), _ctx(), "/a", "/work")

    assert result.success is False
    assert result.exit_code == 2
    assert result.error == "boom"


def test_run_forwards_timeout_and_cwd():
    runner = AgentNodeRunner()
    captured = {}

    def fake_run_subprocess(cmd, *, cwd=".", timeout=None):
        captured["cwd"] = cwd
        captured["timeout"] = timeout
        return 0, "", ""

    with patch("dag_executor.nodes.agent.run_subprocess", fake_run_subprocess):
        runner.run(_node(timeout_seconds=30), _ctx(), "/a", "/mywork")

    assert captured["cwd"] == "/mywork"
    assert captured["timeout"] == 30
