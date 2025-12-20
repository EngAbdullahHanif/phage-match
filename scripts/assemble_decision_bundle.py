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
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from pm.utils import sha256_file, read_tsv, ensure_dir


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def structural_to_score(struct: Optional[Dict[str, Any]]) -> float:
    if not struct:
        return 0.0
    best_e = struct.get("best_evalue")
    hit_count = struct.get("hit_count") or 0
    if best_e is None:
        return 0.0
    try:
        best_e = float(best_e)
    except Exception:
        return 0.0
    if best_e <= 0:
        best_e = 1e-180
    # Map e-values roughly: 1e-2 => 0, 1e-8 => 1
    e_score = clamp01((-math.log10(best_e) - 2.0) / 6.0)
    # Hit saturation (0..1)
    h_score = 1.0 - math.exp(-float(hit_count) / 3.0) if hit_count else 0.0
    return clamp01(0.7 * e_score + 0.3 * h_score)


def similarity_to_score(sim: Optional[Dict[str, Any]]) -> float:
    if not sim:
        return 0.0
    v = sim.get("value")
    try:
        return clamp01(float(v))
    except Exception:
        return 0.0


def safety_penalty(safety: Optional[Dict[str, Any]]) -> float:
    if not safety:
        return 0.0
    flags = safety.get("flags") or []
    penalty = 0.0
    if "vfdb_hit" in flags:
        penalty += 0.25
    if "possible_temperate" in flags:
        penalty += 0.20
    return penalty


def pick_primary_reason(struct_score: float, sim_score: float, flags: List[str]) -> str:
    if flags:
        # still explain best positive evidence, but indicate flags if no strong evidence
        pass
    if struct_score >= sim_score and struct_score > 0.15:
        return "structural_support"
    if sim_score > 0.15:
        return "sequence_similarity"
    return "weak_evidence"


def next_action(flags: List[str]) -> str:
    if "vfdb_hit" in flags:
        return "Manual review recommended: VFDB hit(s) detected. Confirm annotation, exclude if virulence/toxin genes are credible."
    if "possible_temperate" in flags:
        return "Verify lifestyle: integrase/lysogeny markers detected. Prefer strictly lytic phages for therapy; confirm with induction / genome review."
    return "Run plaque assay; if positive, measure EOP and optimize growth conditions."


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def module_status(enabled: bool, test_mode: bool, feature_examples: List[Optional[Dict[str, Any]]], default_tool: str) -> Dict[str, Any]:
    if not enabled:
        return {"status": "skipped", "tool": default_tool, "tool_version": None, "reason": "module disabled"}
    if test_mode:
        return {"status": "mocked", "tool": "mock", "tool_version": None, "reason": None}
    # enabled and not test mode: infer status from features
    statuses = [f.get("status") for f in feature_examples if isinstance(f, dict) and f.get("status")]
    if statuses and all(s == "ok" for s in statuses):
        tool = feature_examples[0].get("tool") if feature_examples and feature_examples[0] else default_tool
        tool_ver = feature_examples[0].get("tool_version") if feature_examples and feature_examples[0] else None
        return {"status": "ok", "tool": tool or default_tool, "tool_version": tool_ver, "reason": None}
    if statuses and any(s in ("unavailable","error") for s in statuses):
        return {"status": "unavailable", "tool": default_tool, "tool_version": None, "reason": "one or more feature artefacts unavailable"}
    # fallback
    return {"status": "unknown", "tool": default_tool, "tool_version": None, "reason": None}


def main() -> None:
    p = argparse.ArgumentParser(description="Assemble Decision Bundle outputs (ranking.csv + evidence_bundle.json) for one host.")
    p.add_argument("--host-id", required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--phage-manifest", required=True)
    p.add_argument("--host-manifest", required=True)
    p.add_argument("--similarity-dir", required=False, default=None)
    p.add_argument("--structural-dir", required=False, default=None)
    p.add_argument("--safety-dir", required=False, default=None)
    p.add_argument("--out-ranking", required=True)
    p.add_argument("--out-evidence", required=True)
    p.add_argument("--pipeline-version", default="0.1.0")
    args = p.parse_args()

    cfg_path = Path(args.config)
    cfg = yaml.safe_load(cfg_path.read_text())

    modules_cfg = cfg.get("modules", {})
    test_mode = bool(modules_cfg.get("test_mode", False))
    enable_similarity = bool(modules_cfg.get("enable_sourmash", False))
    enable_structural = bool(modules_cfg.get("enable_structural_ppi", False))
    enable_safety = bool(modules_cfg.get("enable_safety", False))

    profile = cfg.get("profile", "custom")

    phage_rows = read_tsv(args.phage_manifest)
    phage_ids = [r["phage_id"] for r in phage_rows]

    # Optional: ensure host exists in host manifest
    host_rows = read_tsv(args.host_manifest)
    if not any(r.get("host_id") == args.host_id for r in host_rows):
        raise SystemExit(f"host_id {args.host_id} not found in {args.host_manifest}")

    sim_dir = Path(args.similarity_dir) if args.similarity_dir else None
    struct_dir = Path(args.structural_dir) if args.structural_dir else None
    safety_dir = Path(args.safety_dir) if args.safety_dir else None

    candidates: List[Dict[str, Any]] = []

    for pid in phage_ids:
        sim = load_json(sim_dir / args.host_id / f"{pid}.json") if sim_dir else None
        struct = load_json(struct_dir / args.host_id / f"{pid}.json") if struct_dir else None
        safety = load_json(safety_dir / f"{pid}.json") if safety_dir else None

        sim_score = similarity_to_score(sim)
        struct_score = structural_to_score(struct)
        flags = list((safety or {}).get("flags") or [])
        penalty = safety_penalty(safety)

        # Weighting: structural evidence stronger when available
        confidence = clamp01(0.6 * struct_score + 0.4 * sim_score - penalty)

        reason = pick_primary_reason(struct_score, sim_score, flags)

        candidates.append({
            "host_id": args.host_id,
            "phage_id": pid,
            "confidence_score": confidence,
            "primary_reason": reason,
            "safety_flags": flags,
            "evidence": {
                "similarity": sim,
                "structural": struct,
                "safety": safety,
            },
        })

    # Rank
    candidates.sort(key=lambda r: (-r["confidence_score"], r["phage_id"]))
    for i, c in enumerate(candidates, start=1):
        c["rank"] = i
        c["next_best_action"] = next_action(c["safety_flags"])

    # Write ranking.csv (all candidates)
    out_rank = Path(args.out_ranking)
    ensure_dir(out_rank.parent)
    with out_rank.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["host_id","phage_id","rank","confidence_score","primary_reason","safety_flags"])
        for c in candidates:
            flags = c["safety_flags"]
            flags_str = "none" if not flags else ";".join(flags)
            w.writerow([c["host_id"], c["phage_id"], c["rank"], f"{c['confidence_score']:.4f}", c["primary_reason"], flags_str])

    # Evidence bundle
    top_n = int((cfg.get("params", {}) or {}).get("top_n", 10))
    shortlist = []
    for c in candidates[:top_n]:
        shortlist.append({
            "host_id": c["host_id"],
            "phage_id": c["phage_id"],
            "rank": c["rank"],
            "confidence_score": round(float(c["confidence_score"]), 4),
            "primary_reason": c["primary_reason"],
            "safety_flags": c["safety_flags"],
            "evidence": {
                # Flatten evidence into small UI-friendly objects if present
                "similarity": (c["evidence"]["similarity"] and {
                    "metric": c["evidence"]["similarity"].get("metric"),
                    "value": c["evidence"]["similarity"].get("value"),
                    "status": c["evidence"]["similarity"].get("status"),
                    "tool": c["evidence"]["similarity"].get("tool"),
                }) or None,
                "structural": (c["evidence"]["structural"] and {
                    "hit_count": c["evidence"]["structural"].get("hit_count"),
                    "best_evalue": c["evidence"]["structural"].get("best_evalue"),
                    "best_bitscore": c["evidence"]["structural"].get("best_bitscore"),
                    "qcov_mean": c["evidence"]["structural"].get("qcov_mean"),
                    "tcov_mean": c["evidence"]["structural"].get("tcov_mean"),
                    "status": c["evidence"]["structural"].get("status"),
                    "tool": c["evidence"]["structural"].get("tool"),
                }) or None,
                "safety": (c["evidence"]["safety"] and {
                    "vfdb_hits": c["evidence"]["safety"].get("vfdb_hits"),
                    "integrase_like": c["evidence"]["safety"].get("integrase_like"),
                    "tRNA_count": c["evidence"]["safety"].get("tRNA_count"),
                    "flags": c["evidence"]["safety"].get("flags") or [],
                    "status": c["evidence"]["safety"].get("status"),
                    "tool": c["evidence"]["safety"].get("tool"),
                }) or None,
            },
            "next_best_action": c["next_best_action"],
        })

    run_id = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    pipeline_version = args.pipeline_version + ("-mock" if test_mode else "")

    config_sha = sha256_file(cfg_path)
    manifest_hashes = {
        Path(args.phage_manifest).name: sha256_file(args.phage_manifest),
        Path(args.host_manifest).name: sha256_file(args.host_manifest),
    }

    # Infer module status from a small sample of feature artefacts
    sample_sim = [load_json(sim_dir / args.host_id / f"{phage_ids[0]}.json")] if (sim_dir and phage_ids) else []
    sample_struct = [load_json(struct_dir / args.host_id / f"{phage_ids[0]}.json")] if (struct_dir and phage_ids) else []
    sample_safety = [load_json(safety_dir / f"{phage_ids[0]}.json")] if (safety_dir and phage_ids) else []

    modules = {
        "similarity": module_status(enable_similarity, test_mode, sample_sim, "sourmash"),
        "safety": module_status(enable_safety, test_mode, sample_safety, "abricate"),
        "structural": module_status(enable_structural, test_mode, sample_struct, "foldseek"),
    }

    evidence_bundle = {
        "pipeline_version": pipeline_version,
        "run_id": run_id,
        "host_id": args.host_id,
        "profile": profile,
        "test_mode": test_mode,
        "config_sha256": config_sha,
        "manifest_hashes": manifest_hashes,
        "modules": modules,
        "params": cfg.get("params", {}) or {},
        "versions": cfg.get("versions", {}) or {},
        "shortlist": shortlist,
    }

    out_ev = Path(args.out_evidence)
    ensure_dir(out_ev.parent)
    out_ev.write_text(json.dumps(evidence_bundle, indent=2))


if __name__ == "__main__":
    main()
