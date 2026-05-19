# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 ProtocolWarden
"""
Mock cxrp and rxp so tests run without those packages installed.
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock


def _mock_module(name: str) -> ModuleType:
    mod = ModuleType(name)
    sys.modules[name] = mod
    return mod


for _pkg in ("cxrp", "rxp"):
    if _pkg not in sys.modules:
        top = _mock_module(_pkg)
        for _sub in ("contracts", "vocabulary"):
            child = _mock_module(f"{_pkg}.{_sub}")
            setattr(top, _sub, child)
