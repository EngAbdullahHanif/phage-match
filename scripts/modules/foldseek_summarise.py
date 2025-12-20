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
from typing import Dict, List, Optional

from pm.utils import ensure_dir, stable_float_0_1


def infer_phage_id(target_id: str) -> str:
    # Common patterns:
    #  - P001__prot123
    #  - P001|prot123
    #  - P001
    for sep in ("__", "|"):
        if sep in target_id:
            return target_id.split(sep, 1)[0]
    return target_id.split()[0]


def parse_hits(tsv_path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for line in tsv_path.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        # Expected format: query, target, evalue, bitscore, qcov, tcov (others tolerated)
        if len(parts) < 4:
            continue
        row = {
            "query": parts[0],
            "target": parts[1],
            "evalue": parts[2],
            "bitscore": parts[3],
            "qcov": parts[4] if len(parts) > 4 else None,
            "tcov": parts[5] if len(parts) > 5 else None,
        }
        rows.append(row)
    return rows


def safe_float(x: Optional[str]) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None


def main() -> None:
    p = argparse.ArgumentParser(description="Summarise Foldseek hits into per host×phage structural.json features.")
    p.add_argument("--host-id", required=True)
    p.add_argument("--phage-ids", required=True, help="Comma-separated list of phage_ids to emit.")
    p.add_argument("--hits-tsv", required=False, help="Foldseek hits TSV (query\ttarget\tevalue\tbitscore[\tqcov\ttcov...])")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--tool-version", default=None)
    p.add_argument("--mock", action="store_true")
    args = p.parse_args()

    out_dir = ensure_dir(args.out_dir)
    phage_ids = [p.strip() for p in args.phage_ids.split(",") if p.strip()]

    if args.mock or not args.hits_tsv:
        for pid in phage_ids:
            # Deterministic plausible mock
            base = stable_float_0_1(f"structural::{args.host_id}::{pid}")
            hit_count = int(base * 6)  # 0..5
            best_evalue = 10 ** (-(2 + int(base * 6))) if hit_count > 0 else None
            payload = {
                "host_id": args.host_id,
                "phage_id": pid,
                "hit_count": hit_count,
                "best_evalue": best_evalue,
                "best_bitscore": 50.0 + 200.0 * base if hit_count > 0 else None,
                "qcov_mean": 0.1 + 0.8 * base if hit_count > 0 else None,
                "tcov_mean": 0.1 + 0.8 * base if hit_count > 0 else None,
                "top_targets": [],
                "tool": "mock",
                "tool_version": None,
                "status": "mocked",
                "reason": None,
            }
            (out_dir / f"{pid}.json").write_text(json.dumps(payload, indent=2))
        return

    tsv = Path(args.hits_tsv)
    if not tsv.exists():
        for pid in phage_ids:
            payload = {
                "host_id": args.host_id,
                "phage_id": pid,
                "hit_count": 0,
                "best_evalue": None,
                "best_bitscore": None,
                "qcov_mean": None,
                "tcov_mean": None,
                "top_targets": [],
                "tool": "foldseek",
                "tool_version": args.tool_version,
                "status": "unavailable",
                "reason": f"missing hits file: {tsv}",
            }
            (out_dir / f"{pid}.json").write_text(json.dumps(payload, indent=2))
        return

    hits = parse_hits(tsv)

    grouped: Dict[str, List[Dict[str, str]]] = {}
    for row in hits:
        pid = infer_phage_id(row["target"])
        grouped.setdefault(pid, []).append(row)

    for pid in phage_ids:
        rows = grouped.get(pid, [])
        evalues = [safe_float(r["evalue"]) for r in rows]
        bits = [safe_float(r["bitscore"]) for r in rows]
        qcovs = [safe_float(r.get("qcov")) for r in rows]
        tcovs = [safe_float(r.get("tcov")) for r in rows]

        evalues_f = [v for v in evalues if v is not None]
        bits_f = [v for v in bits if v is not None]
        qcovs_f = [v for v in qcovs if v is not None]
        tcovs_f = [v for v in tcovs if v is not None]

        # Sort by best evalue
        top = []
        for r in sorted(rows, key=lambda r: safe_float(r["evalue"]) if safe_float(r["evalue"]) is not None else 1e9)[:5]:
            top.append({
                "query": r["query"],
                "target": r["target"],
                "evalue": safe_float(r["evalue"]),
                "bitscore": safe_float(r["bitscore"]),
                "qcov": safe_float(r.get("qcov")),
                "tcov": safe_float(r.get("tcov")),
            })

        payload = {
            "host_id": args.host_id,
            "phage_id": pid,
            "hit_count": len(rows),
            "best_evalue": min(evalues_f) if evalues_f else None,
            "best_bitscore": max(bits_f) if bits_f else None,
            "qcov_mean": sum(qcovs_f) / len(qcovs_f) if qcovs_f else None,
            "tcov_mean": sum(tcovs_f) / len(tcovs_f) if tcovs_f else None,
            "top_targets": top,
            "tool": "foldseek",
            "tool_version": args.tool_version,
            "status": "ok",
            "reason": None,
        }
        (out_dir / f"{pid}.json").write_text(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
