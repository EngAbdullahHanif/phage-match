#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import List

from jsonschema import Draft202012Validator


REQUIRED_RANKING_COLS = ["host_id","phage_id","rank","confidence_score","primary_reason","safety_flags"]


def validate_ranking_csv(path: Path) -> List[str]:
    errors: List[str] = []
    with path.open(newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return ["ranking.csv is empty"]
        if header != REQUIRED_RANKING_COLS:
            errors.append(f"ranking.csv header mismatch. Expected {REQUIRED_RANKING_COLS} but got {header}")
        for i, row in enumerate(reader, start=2):
            if len(row) != len(REQUIRED_RANKING_COLS):
                errors.append(f"ranking.csv row {i} has {len(row)} columns (expected {len(REQUIRED_RANKING_COLS)})")
                continue
            # basic type checks
            try:
                int(row[2])
            except Exception:
                errors.append(f"ranking.csv row {i}: rank is not an int: {row[2]}")
            try:
                float(row[3])
            except Exception:
                errors.append(f"ranking.csv row {i}: confidence_score is not a float: {row[3]}")
    return errors


def validate_evidence_json(evidence_path: Path, schema_path: Path) -> List[str]:
    errors: List[str] = []
    schema = json.loads(schema_path.read_text())
    evidence = json.loads(evidence_path.read_text())
    validator = Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(evidence), key=str):
        errors.append(err.message)
    return errors


def main() -> None:
    p = argparse.ArgumentParser(description="Validate Decision Bundle outputs against schema and required columns.")
    p.add_argument("--ranking", required=True)
    p.add_argument("--evidence", required=True)
    p.add_argument("--schema", required=True)
    args = p.parse_args()

    ranking_path = Path(args.ranking)
    evidence_path = Path(args.evidence)
    schema_path = Path(args.schema)

    errs = []
    errs.extend(validate_ranking_csv(ranking_path))
    errs.extend(validate_evidence_json(evidence_path, schema_path))

    if errs:
        print("VALIDATION FAILED")
        for e in errs:
            print(f"- {e}")
        raise SystemExit(2)

    print("VALIDATION OK")


if __name__ == "__main__":
    main()
