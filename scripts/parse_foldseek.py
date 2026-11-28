"""Add a schema to the default twelve-column Foldseek easy-search TSV."""

import argparse
import csv
from pathlib import Path


COLUMNS = (
    "query", "target", "identity", "alignment_length", "mismatches", "gap_opens",
    "query_start", "query_end", "target_start", "target_end", "evalue", "bit_score",
)


def write_structural_similarity(source, destination):
    with Path(source).open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream, delimiter="\t")
        rows = []
        for row in reader:
            if not row:
                continue
            if len(row) != len(COLUMNS):
                raise ValueError(f"{source}:{reader.line_num} expected {len(COLUMNS)} Foldseek columns")
            rows.append(row)
    with Path(destination).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("destination")
    args = parser.parse_args()
    try:
        write_structural_similarity(args.source, args.destination)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Foldseek TSV error: {exc}\n")
