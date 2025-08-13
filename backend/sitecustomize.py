"""Ensure project root is on sys.path when running from the backend/ directory.

This helps imports like `backend.main` work when tools launch from `backend/`.
"""

from __future__ import annotations

import os
import sys

backend_dir = os.path.dirname(__file__)
project_root = os.path.dirname(backend_dir)
if project_root and project_root not in sys.path:
    sys.path.insert(0, project_root)


