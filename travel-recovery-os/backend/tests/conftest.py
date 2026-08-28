"""
conftest.py — pytest bootstrap for the SynapseAir backend test suite.

Makes the ``backend`` package importable regardless of the directory pytest
is invoked from (repo root via ``python -m pytest backend/tests`` or the
backend directory itself, as CI does with ``working-directory: ./backend``).
"""
import sys
from pathlib import Path

# backend/tests/conftest.py -> repo root is three levels up.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
