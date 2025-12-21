#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def iso_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_ranking(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def load_evidence(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text())


def next_action_for(phage_id: str, evidence: Dict[str, object]) -> Optional[str]:
    shortlist = evidence.get("shortlist") or []
    for item in shortlist:
        if item.get("phage_id") == phage_id:
            return item.get("next_best_action")
    return None


def main() -> None:
    p = argparse.ArgumentParser(description="Generate a lightweight test plan markdown from ranking + evidence bundle.")
    p.add_argument("--ranking", required=True)
    p.add_argument("--evidence", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--top-n", type=int, default=10)
    args = p.parse_args()

    ranking = load_ranking(Path(args.ranking))
    evidence = load_evidence(Path(args.evidence))

    host_id = None
    if ranking:
        host_id = ranking[0].get("host_id")
    host_id = host_id or evidence.get("host_id") or "unknown"

    lines: List[str] = []
    lines.append(f"# Test plan for host {host_id}")
    lines.append("")
    lines.append(f"Generated: {iso_utc()}")
    lines.append("")
    lines.append("## Top candidates")
    lines.append("")
    top = ranking[: max(0, args.top_n)]
    if not top:
        lines.append("_No ranking rows found._")
    else:
        lines.append("| Rank | Phage | Confidence | Primary reason | Next best action |")
        lines.append("| ---- | ----- | ---------- | -------------- | ---------------- |")
        for row in top:
            rank = row.get("rank", "")
            phage = row.get("phage_id", "")
            conf = row.get("confidence_score", "")
            reason = row.get("primary_reason", "")
            action = next_action_for(phage, evidence) or "Not provided"
            lines.append(f"| {rank} | {phage} | {conf} | {reason} | {action} |")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
