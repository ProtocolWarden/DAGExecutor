# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
"""
Test bootstrap.

- Enforces that tests run inside this project's virtual environment (S4).
- Makes the sibling ``core_runner`` package importable without installing it.
- Mocks the ``cxrp`` and ``rxp`` contract packages so importing
  ``core_runner.process`` (the only core_runner surface DAGExecutor uses)
  does not pull in the full RxP/CxRP contract stack.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

# --- venv guard (S4) -------------------------------------------------------
_REPO_ROOT = Path(__file__).parent.parent.resolve()
_EXPECTED_VENV = (_REPO_ROOT / ".venv").resolve()
_ACTIVE_PREFIX = Path(sys.prefix).resolve()
_IN_CI = os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS")

if _EXPECTED_VENV.is_dir() and not _IN_CI and _ACTIVE_PREFIX != _EXPECTED_VENV:
    raise SystemExit(
        f"ERROR: Tests must be run inside this project's virtual environment.\n"
        f"Expected: {_EXPECTED_VENV}\n"
        f"Active:   {_ACTIVE_PREFIX}\n\n"
        f"Activate it first:\n"
        f"  source .venv/bin/activate\n"
        f"Or invoke pytest through the venv directly:\n"
        f"  .venv/bin/pytest"
    )

# --- sibling core_runner on path -------------------------------------------
_core_runner_src = _REPO_ROOT.parent / "CoreRunner" / "src"
if str(_core_runner_src) not in sys.path:
    sys.path.insert(0, str(_core_runner_src))


class _AnyAttrModule(ModuleType):
    """Module whose every accessed attribute is a fresh MagicMock."""

    def __getattr__(self, name: str) -> object:
        value = MagicMock(name=f"{self.__name__}.{name}")
        setattr(self, name, value)
        return value


def _mock_module(name: str) -> ModuleType:
    mod = _AnyAttrModule(name)
    sys.modules[name] = mod
    return mod


for _pkg in ("cxrp", "rxp"):
    if _pkg not in sys.modules:
        top = _mock_module(_pkg)
        for _sub in ("contracts", "vocabulary"):
            child = _mock_module(f"{_pkg}.{_sub}")
            setattr(top, _sub, child)
