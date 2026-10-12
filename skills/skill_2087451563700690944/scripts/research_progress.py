#!/usr/bin/env python3
from __future__ import annotations

import sys
import zlib
from pathlib import Path

_FILE = Path(__file__).resolve()
_SKILL = _FILE.parents[1]
_SCRIPTS = _SKILL / "scripts"
for _p in (_SCRIPTS, _SKILL):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
_code = zlib.decompress(_FILE.with_suffix(".pyz").read_bytes())
exec(compile(_code, str(_FILE), "exec"), globals())
