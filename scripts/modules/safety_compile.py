#!/usr/bin/env python3
from __future__ import annotations

# Ensure repo root is on sys.path when running as a script (python path/to/script.py)
import sys
from pathlib import Path
_REPO_ROOT = None
for _p in Path(__file__).resolve().parents:
    if (_p / "config.yaml").exists() and (_p / "contracts").exists():
        _REPO_ROOT = _p
        break
if _REPO_ROOT:
    sys.path.insert(0, str(_REPO_ROOT))

import argparse
import json
from pathlib import Path
from typing import Optional, List

from pm.utils import ensure_dir, stable_float_0_1


def count_abricate_hits(tsv: Path) -> int:
    if not tsv.exists():
        return 0
    lines = [l for l in tsv.read_text().splitlines() if l.strip()]
    if not lines:
        return 0
    # Abricate TSV usually starts with a header line beginning with '#FILE' or 'FILE'
    data = [l for l in lines if not l.startswith("#") and not l.lower().startswith("file\t")]
    return len(data)


def parse_gff_for_flags(gff: Path) -> tuple[Optional[int], bool]:
    if not gff or not gff.exists():
        return None, False
    trna = 0
    integrase_like = False
    for line in gff.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 9:
            continue
        ftype = parts[2]
        attrs = parts[8].lower()
        if ftype.lower() == "trna":
            trna += 1
        # conservative keyword scan
        if "integrase" in attrs or "site-specific recombinase" in attrs:
            integrase_like = True
    return trna, integrase_like


def main() -> None:
    p = argparse.ArgumentParser(description="Compile safety feature (abricate + lysogeny flags) for a phage.")
    p.add_argument("--phage-id", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--abricate-tsv", default=None)
    p.add_argument("--gff", default=None)
    p.add_argument("--abricate-version", default=None)
    p.add_argument("--mock", action="store_true")
    args = p.parse_args()

    out = Path(args.out)
    ensure_dir(out.parent)

    if args.mock:
        base = stable_float_0_1(f"safety::{args.phage_id}")
        vfdb_hits = int(base * 3)  # 0..2
        integrase_like = base > 0.6
        trna_count = int(base * 2)  # 0..1
        flags: List[str] = []
        if vfdb_hits > 0:
            flags.append("vfdb_hit")
        if integrase_like:
            flags.append("possible_temperate")
        payload = {
            "phage_id": args.phage_id,
            "vfdb_hits": vfdb_hits,
            "integrase_like": integrase_like,
            "tRNA_count": trna_count,
            "flags": flags,
            "tool": "mock",
            "tool_version": None,
            "status": "mocked",
            "reason": None,
        }
        out.write_text(json.dumps(payload, indent=2))
        return

    vfdb_hits = 0
    trna_count: Optional[int] = None
    integrase_like = False
    reason: Optional[str] = None
    status = "ok"

    try:
        if args.abricate_tsv:
            vfdb_hits = count_abricate_hits(Path(args.abricate_tsv))
        if args.gff:
            trna_count, integrase_like = parse_gff_for_flags(Path(args.gff))
    except Exception as e:
        status = "unavailable"
        reason = f"safety parsing failed: {e}"

    flags: List[str] = []
    if vfdb_hits > 0:
        flags.append("vfdb_hit")
    if integrase_like:
        flags.append("possible_temperate")

    payload = {
        "phage_id": args.phage_id,
        "vfdb_hits": vfdb_hits,
        "integrase_like": integrase_like,
        "tRNA_count": trna_count,
        "flags": flags,
        "tool": "abricate/prokka",
        "tool_version": args.abricate_version,
        "status": status,
        "reason": reason,
    }
    out.write_text(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
