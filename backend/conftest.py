"""Pytest configuration for the backend test suite.

Adds the backend root directory to sys.path so that ``from main import create_app``
and ``from app.* import ...`` work regardless of where pytest is invoked from.
"""

import sys
from pathlib import Path

# backend/ is the directory containing this conftest.py
_backend_root = str(Path(__file__).resolve().parent)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)
