# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
"""Unit tests for dag_executor.config (environment-access layer)."""
from __future__ import annotations

import os
from unittest.mock import patch

from dag_executor.config import child_env


def test_child_env_copies_current_environment():
    with patch.dict(os.environ, {"FOO": "bar"}, clear=False):
        env = child_env()
    assert env["FOO"] == "bar"


def test_child_env_returns_a_copy_not_the_live_mapping():
    env = child_env()
    env["INJECTED_ONLY_IN_COPY"] = "1"
    assert "INJECTED_ONLY_IN_COPY" not in os.environ


def test_child_env_applies_overrides_on_top():
    with patch.dict(os.environ, {"KEEP": "1"}, clear=False):
        env = child_env({"ITEM": "alpha"})
    assert env["ITEM"] == "alpha"
    assert env["KEEP"] == "1"


def test_overrides_win_over_inherited_value():
    with patch.dict(os.environ, {"DUP": "old"}, clear=False):
        env = child_env({"DUP": "new"})
    assert env["DUP"] == "new"


def test_none_overrides_is_noop():
    with patch.dict(os.environ, {"X": "y"}, clear=False):
        env = child_env(None)
    assert env["X"] == "y"
