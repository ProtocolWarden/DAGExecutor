# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
"""Unit tests for dag_executor.cli."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from dag_executor import cli


def test_run_command_succeeds_exits_zero(capsys):
    fake_result = {"status": "succeeded", "metadata": {}}

    class FakeRunner:
        def __init__(self, **kw):
            self.kw = kw

        def run_from_yaml(self, path, goal_text=""):
            assert path == "wf.yaml"
            assert goal_text == "do it"
            return fake_result

    argv = ["dag-executor", "run", "wf.yaml", "--goal", "do it"]
    with patch.object(cli.sys, "argv", argv), patch.object(
        cli, "DAGExecutorRunner", FakeRunner
    ):
        with pytest.raises(SystemExit) as exc:
            cli.app()

    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert json.loads(out)["status"] == "succeeded"


def test_run_command_failure_exits_one():
    class FakeRunner:
        def __init__(self, **kw):
            pass

        def run_from_yaml(self, path, goal_text=""):
            return {"status": "failed", "metadata": {}}

    argv = ["dag-executor", "run", "wf.yaml"]
    with patch.object(cli.sys, "argv", argv), patch.object(
        cli, "DAGExecutorRunner", FakeRunner
    ):
        with pytest.raises(SystemExit) as exc:
            cli.app()

    assert exc.value.code == 1


def test_runner_constructed_with_cli_dirs():
    captured = {}

    class FakeRunner:
        def __init__(self, **kw):
            captured.update(kw)

        def run_from_yaml(self, path, goal_text=""):
            return {"status": "succeeded"}

    argv = [
        "dag-executor",
        "run",
        "wf.yaml",
        "--artifacts-dir",
        "/tmp/art",
        "--working-dir",
        "/tmp/work",
    ]
    with patch.object(cli.sys, "argv", argv), patch.object(
        cli, "DAGExecutorRunner", FakeRunner
    ):
        with pytest.raises(SystemExit):
            cli.app()

    assert captured["artifacts_dir"] == "/tmp/art"
    assert captured["working_directory"] == "/tmp/work"


def test_no_subcommand_prints_help_and_exits_one(capsys):
    argv = ["dag-executor"]
    with patch.object(cli.sys, "argv", argv):
        with pytest.raises(SystemExit) as exc:
            cli.app()

    assert exc.value.code == 1
    assert "usage" in capsys.readouterr().out.lower()
