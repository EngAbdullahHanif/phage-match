"""Validate a proposed table's column names against the reviewed feature manifest."""

import argparse
import csv
from pathlib import Path

import yaml


ID_COLUMNS = {"host_id", "phage_id"}
ASSAY_COLUMNS = {"category", "binary", "virulence_index", "inhibition_efficiency"}
FEATURE_ROLES = {"host", "phage", "pair"}


def validate_columns(header, manifest):
    if not isinstance(manifest, dict) or manifest.get("version") != 1:
        raise ValueError("Expected feature manifest version 1")
    allowed = manifest.get("columns")
    if not isinstance(allowed, dict):
        raise ValueError("Feature manifest columns must be a mapping")
    blocked = ASSAY_COLUMNS & (set(header) | allowed.keys())
    if blocked:
        raise ValueError(f"Assay-derived columns are blocked: {', '.join(sorted(blocked))}")
    for name, entry in allowed.items():
        if (not isinstance(name, str) or not name or name in ID_COLUMNS or not isinstance(entry, dict)
                or not all(isinstance(entry.get(key), str) and entry[key].strip() for key in ("source", "dtype", "role"))
                or entry["role"] not in FEATURE_ROLES):
            raise ValueError(f"Invalid feature registration: {name}")
    if not header or len(set(header)) != len(header):
        raise ValueError("Expected a nonempty header with unique columns")
    unknown = set(header) - ID_COLUMNS - allowed.keys()
    if unknown:
        raise ValueError(f"Unregistered feature columns: {', '.join(sorted(unknown))}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("table", type=Path, help="CSV or TSV file")
    parser.add_argument("--manifest", type=Path, default=Path("features_manifest.yaml"))
    args = parser.parse_args()
    try:
        manifest = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
        with args.table.open(encoding="utf-8-sig", newline="") as stream:
            delimiter = "\t" if args.table.suffix.lower() == ".tsv" else ","
            validate_columns(next(csv.reader(stream, delimiter=delimiter), []), manifest)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        parser.exit(2, f"Feature manifest error: {exc}\n")


if __name__ == "__main__":
    main()
