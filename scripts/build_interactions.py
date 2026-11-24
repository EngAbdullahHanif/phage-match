"""Preserve assay observations and audit local file coverage without reading sequences."""

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

from openpyxl import load_workbook


FIELDS = (
    "host_id_raw", "phage_id_raw", "host_id", "phage_id", "category", "binary",
    "source_file", "source_sheet", "assay_type", "notes",
)
SCORES = {"category": range(4), "binary": range(2)}
FASTA = {".fna", ".fasta", ".fa"}


def normalize_id(value):
    raw = str(value)
    clean = raw.strip()
    if re.fullmatch(r"\d+\.0+", clean):
        clean = clean.split(".", 1)[0]
    return raw, clean


def blank(value):
    return value is None or isinstance(value, str) and not value.strip()


def read_sheet(sheet, source):
    rows = iter(sheet.values)
    headers = {}
    for column, value in enumerate(next(rows, ())[1:], start=1):
        if blank(value):
            continue
        raw, key = normalize_id(value)
        if any(key == previous[1] for previous in headers.values()):
            raise ValueError(f"{source}[{sheet.title}] duplicate column ID: {key}")
        headers[column] = (raw, key)
    if not headers:
        raise ValueError(f"{source}[{sheet.title}] has no named assay columns")

    scores = {}
    host_ids = set()
    ignored_cells = 0
    rows_without_ids = []
    for index, row in enumerate(rows, start=2):
        if not row or all(blank(value) for value in row):
            continue
        ignored_cells += sum(not blank(value) and column not in headers
                             for column, value in enumerate(row[1:], start=1))
        if blank(row[0]):
            if any(column < len(row) and not blank(row[column]) for column in headers):
                rows_without_ids.append(index)
            continue
        raw_host, host = normalize_id(row[0])
        host_ids.add(host)
        for column, value in enumerate(row[1:], start=1):
            if blank(value) or column not in headers:
                continue
            raw_phage, phage = headers[column]
            score = str(value).strip()
            if not re.fullmatch(r"[0-9](?:\.0+)?", score) or int(float(score)) not in SCORES[sheet.title]:
                raise ValueError(f"{source}[{sheet.title}] invalid score at row {index}, column {column + 1}")
            key = (host, phage)
            raw_and_score = (raw_host, raw_phage, int(float(score)))
            if key in scores:
                raise ValueError(f"{source}[{sheet.title}] duplicate observations for {host} / {phage}")
            scores[key] = raw_and_score
    return scores, host_ids, {key for _, key in headers.values()}, ignored_cells, rows_without_ids


def read_assays(paths):
    records = []
    ids = {"host": set(), "phage": set()}
    audit = []
    for path in paths:
        workbook = load_workbook(path, read_only=True, data_only=True)
        try:
            if missing := SCORES.keys() - set(workbook.sheetnames):
                raise ValueError(f"{path.name} is missing worksheet(s): {', '.join(sorted(missing))}")
            category, binary = (read_sheet(workbook[name], path.name) for name in SCORES)
        finally:
            workbook.close()
        for _, hosts, phages, _, _ in (category, binary):
            ids["host"].update(hosts)
            ids["phage"].update(phages)
        category_scores, _, category_ids, category_ignored, category_orphans = category
        binary_scores, _, binary_ids, binary_ignored, binary_orphans = binary
        audit.append((path.name, category_ignored, binary_ignored, category_ids ^ binary_ids,
                      category_orphans, binary_orphans))
        for host, phage in sorted(category_scores.keys() | binary_scores.keys()):
            first = category_scores.get((host, phage))
            second = binary_scores.get((host, phage))
            raw_host, raw_phage, _ = first or second
            sheets = ",".join(name for name, score in zip(SCORES, (first, second)) if score is not None)
            notes = ""
            if first and second and first[:2] != second[:2]:
                notes = f"binary raw IDs: {second[0]!r}, {second[1]!r}"
            records.append((raw_host, raw_phage, host, phage, first[2] if first else None,
                            second[2] if second else None, path.name, sheets, "spot_test", notes))
    return records, ids, audit


def file_coverage(ids, roots, aliases_path=None):
    mappings = defaultdict(dict)
    if aliases_path:
        with aliases_path.open(newline="", encoding="utf-8-sig") as stream:
            fields = ("role", "source_id", "target_id", "evidence")
            reader = csv.DictReader(stream, delimiter="\t")
            if tuple(reader.fieldnames or ()) != fields:
                raise ValueError(f"{aliases_path} must use these columns: {', '.join(fields)}")
            for row in reader:
                role, source, target, evidence = ((row[key] or "").strip() for key in fields)
                if role == "prophage":
                    continue
                if role not in roots or not all((source, target, evidence)) or source in mappings[role]:
                    raise ValueError(f"Invalid or duplicate alias for {role}: {source}")
                mappings[role][source] = (target, evidence)

    entries = []
    for role, root in roots.items():
        files = {}
        for path in sorted(root.iterdir()):
            if path.suffix.lower() not in FASTA or not path.is_file():
                continue
            if not path.resolve().is_relative_to(root.resolve()) or path.stem in files:
                raise ValueError(f"Invalid or duplicate {role} input: {path}")
            files[path.stem] = path
        used = set()
        for name in sorted(ids[role]):
            target, evidence = mappings[role].get(name, (name, "Exact ID"))
            if name in files and target != name:
                raise ValueError(f"Documented {role} alias conflicts with exact match: {name}")
            if target in files:
                entries.append((role, name, target, str(files[target]), "matched", evidence))
                used.add(target)
            else:
                entries.append((role, name, target, "", "genome_missing", ""))
        for name in sorted(files.keys() - used):
            entries.append((role, "", name, str(files[name]), "label_missing", ""))
    return entries


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(fields)
        writer.writerows(rows)


def inventory_text(records, coverage, audit):
    matched = {role: {row[1] for row in coverage if row[0] == role and row[4] == "matched"}
               for role in ("host", "phage")}
    covered = sum(row[2] in matched["host"] and row[3] in matched["phage"] for row in records)
    lines = ["# Assay data inventory", "", f"- Observed pairs per source workbook, summed: {len(records)}",
             f"- Distinct normalized pairs across workbooks: {len({row[2:4] for row in records})}",
             f"- Observations with confirmed local IDs on both sides: {covered}",
             f"- Observations with unresolved local IDs: {len(records) - covered}",
             "- Binary positive counts use the workbook's recorded value of 1.", ""]
    for name, column in (("Category", 4), ("Binary", 5)):
        counts = Counter(row[column] for row in records)
        values = ", ".join(f"{key}: {counts[key]}" for key in sorted(counts.keys() - {None}))
        lines.extend((f"- {name} counts: {values or 'none'} · blank: {counts[None]}",))
    for role, index in (("host", 2), ("phage", 3)):
        totals = Counter(row[index] for row in records if row[5] is not None)
        positives = Counter(row[index] for row in records if row[5] == 1)
        lines.extend(("", f"## Recorded binary positives by {role}", ""))
        lines.extend(f"- `{name}`: {positives[name]} / {totals[name]}" for name in sorted(totals))
        unresolved = [row[1] for row in coverage if row[0] == role and row[4] == "genome_missing"]
        lines.extend(("", f"### Unresolved {role} IDs ({len(unresolved)})", "",
                      ", ".join(f"`{name}`" for name in unresolved) or "None"))
    lines.extend(("", "## Workbook review", ""))
    for workbook, cat_ignored, bin_ignored, differences, cat_orphans, bin_orphans in audit:
        headers = ", ".join(sorted(differences)) or "none"
        lines.append(f"- `{workbook}` · populated cells under unnamed columns: category {cat_ignored}, "
                     f"binary {bin_ignored} · header differences: {headers} · rows with scores and no host ID: "
                     f"category {cat_orphans}, binary {bin_orphans}")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbooks", nargs="+", type=Path)
    parser.add_argument("--host-dir", type=Path, default=Path("data/genomes_id"))
    parser.add_argument("--phage-dir", type=Path, default=Path("data/phage_genome"))
    parser.add_argument("--aliases", type=Path)
    parser.add_argument("--interactions", type=Path, default=Path("data/interim/interactions.csv"))
    parser.add_argument("--crosswalk", type=Path, default=Path("data/meta_data/id_crosswalk.csv"))
    parser.add_argument("--report", type=Path, default=Path("reports/data_inventory.md"))
    parser.add_argument("--allow-unresolved", action="store_true", help="Return success with unresolved IDs")
    args = parser.parse_args(argv)
    try:
        if len({path.name for path in args.workbooks}) != len(args.workbooks):
            raise ValueError("Workbook basenames must be distinct for provenance")
        inputs = {path.resolve() for path in args.workbooks}
        if args.aliases:
            inputs.add(args.aliases.resolve())
        outputs = {path.resolve() for path in (args.interactions, args.crosswalk, args.report)}
        if len(outputs) != 3 or inputs & outputs:
            raise ValueError("Output paths must be distinct and separate from source files")
        records, ids, audit = read_assays(args.workbooks)
        coverage = file_coverage(ids, {"host": args.host_dir, "phage": args.phage_dir}, args.aliases)
        write_csv(args.interactions, FIELDS, records)
        write_csv(args.crosswalk, ("role", "label_id", "genome_id", "path", "status", "evidence"), coverage)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(inventory_text(records, coverage, audit), encoding="utf-8")
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(2, f"Assay inventory error: {exc}\n")
    unresolved = sum(row[4] != "matched" for row in coverage)
    print(f"Wrote {len(records)} observations and {len(coverage)} crosswalk entries. Unresolved IDs: {unresolved}.")
    if unresolved and not args.allow_unresolved:
        parser.exit(2, "Crosswalk has unresolved IDs. Review the generated report.\n")


if __name__ == "__main__":
    main()
