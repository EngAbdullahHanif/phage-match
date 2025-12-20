#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Dict, List, Any


def sha256_file(path: str | Path) -> str:
    p = Path(path)
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_tsv(path: str | Path) -> List[Dict[str, str]]:
    p = Path(path)
    with p.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return [dict(row) for row in reader]


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def stable_float_0_1(seed: str) -> float:
    """Deterministically map a string seed to a pseudo-random float in [0,1)."""
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    # use 8 hex chars => 32-bit int
    n = int(h[:8], 16)
    return (n % 10_000_000) / 10_000_000.0
