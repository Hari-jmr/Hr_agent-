#!/usr/bin/env python3
"""Compatibility entry point for PDF2 index preflight/rebuild.

The historical incremental seeder could mix an old corpus with another folder.
It now uses the same PDF2-only preflight/rebuild workflow as reingest.py. It
never reads or modifies the retained legacy tables.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.index_common import main

if __name__ == "__main__":
    main("Preflight or build a staged PDF2 index (legacy seeder entry point)")
