# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
"""Centralised environment access for DAGExecutor.

All raw ``os.environ`` reads are funnelled through this module so that
environment handling stays in one place (easier to audit, mock in tests,
and reason about for secret isolation). Node runners must not touch
``os.environ`` directly.
"""
from __future__ import annotations

import os


def child_env(overrides: dict[str, str] | None = None) -> dict[str, str]:
    """Return a copy of the current process environment for a child process.

    A copy is returned (never the live ``os.environ`` mapping) so callers may
    mutate it freely without affecting the parent. ``overrides`` are applied
    on top of the inherited values.
    """
    env = dict(os.environ)
    if overrides:
        env.update(overrides)
    return env
