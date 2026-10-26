#!/usr/bin/env python3
"""Preflight/build the PDF2 corpus used by the application.

The legacy documents/chunks tables are never touched by this script. Run without
--build-candidate for preflight only; with that flag, the PDF2 corpus tables are
rebuilt atomically and become the application's active retrieval corpus.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.index_common import main

if __name__ == "__main__":
    main("Preflight or build a staged PDF2 index")
