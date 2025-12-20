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
import subprocess
from pathlib import Path
from typing import Optional

from pm.utils import ensure_dir, stable_float_0_1


def run_compare(host_sig: Path, phage_sig: Path, tmp_csv: Path) -> float:
    cmd = [
        "sourmash", "compare",
        "--containment",
        str(host_sig),
        str(phage_sig),
        "--csv", str(tmp_csv),
    ]
    subprocess.run(cmd, check=True)
    lines = tmp_csv.read_text().strip().splitlines()
    if len(lines) < 3:
        raise RuntimeError(f"Unexpected sourmash CSV format: {tmp_csv}")
    row1 = lines[1].split(",")
    row2 = lines[2].split(",")
    vals = []
    for row in (row1, row2):
        for cell in row[1:]:
            try:
                vals.append(float(cell))
            except ValueError:
                pass
    return max(vals) if vals else 0.0


def main() -> None:
    p = argparse.ArgumentParser(description="Compute sourmash containment similarity feature (per host×phage).")
    p.add_argument("--host-id", required=True)
    p.add_argument("--phage-id", required=True)
    p.add_argument("--host-sig", required=False, default=None)
    p.add_argument("--phage-sig", required=False, default=None)
    p.add_argument("--out", required=True)
    p.add_argument("--tool-version", default=None)
    p.add_argument("--mock", action="store_true")
    args = p.parse_args()

    out = Path(args.out)
    ensure_dir(out.parent)

    if args.mock:
        value = stable_float_0_1(f"similarity::{args.host_id}::{args.phage_id}")
        payload = {
            "host_id": args.host_id,
            "phage_id": args.phage_id,
            "metric": "mock_containment",
            "value": round(value, 4),
            "tool": "mock",
            "tool_version": None,
            "status": "mocked",
            "reason": None,
        }
        out.write_text(json.dumps(payload, indent=2))
        return

    if not args.host_sig or not args.phage_sig:
        raise SystemExit("--host-sig and --phage-sig are required unless --mock is set.")

    host_sig = Path(args.host_sig)
    phage_sig = Path(args.phage_sig)
    tmp_csv = out.with_suffix(".tmp.csv")

    try:
        value = run_compare(host_sig, phage_sig, tmp_csv)
        status = "ok"
        reason: Optional[str] = None
    except Exception as e:
        value = 0.0
        status = "unavailable"
        reason = f"sourmash compare failed: {e}"
    finally:
        if tmp_csv.exists():
            tmp_csv.unlink()

    payload = {
        "host_id": args.host_id,
        "phage_id": args.phage_id,
        "metric": "containment",
        "value": float(value),
        "tool": "sourmash",
        "tool_version": args.tool_version,
        "status": status,
        "reason": reason,
    }
    out.write_text(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
