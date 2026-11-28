"""Preserve assay observations and audit local file coverage without reading sequences."""

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter


FIELDS = (
    "host_id_raw", "phage_id_raw", "host_id", "phage_id", "category", "binary",
    "source_file", "source_sheet", "assay_type", "notes",
)
SCORES = {"category": range(4), "binary": range(2)}
FASTA = {".fna", ".fasta", ".fa"}
QC_FIELDS = ("workbook", "sheet", "cell", "severity", "code", "detail")
ALIAS_FIELDS = ("role", "source_id", "target_id", "evidence")
REVIEW_STATES = {"confirmed", "pending", "rejected"}


def normalize_id(value):
    raw = str(value)
    clean = raw.strip()
    if re.fullmatch(r"\d+\.0+", clean):
        clean = clean.split(".", 1)[0]
    return raw, clean


def blank(value):
    return value is None or isinstance(value, str) and not value.strip()


def qc_issue(issues, workbook, sheet, row, column, code, detail, *, severity="review"):
    cell = f"{get_column_letter(column + 1)}{row}"
    issues.append((workbook, sheet, cell, severity, code, detail))


def read_sheet(sheet, source, issues):
    rows = iter(sheet.values)
    headers = {}
    header_columns = {}
    for column, value in enumerate(next(rows, ())[1:], start=1):
        if blank(value):
            continue
        raw, key = normalize_id(value)
        if key in header_columns:
            first = get_column_letter(header_columns[key] + 1)
            qc_issue(issues, source, sheet.title, 1, column, "duplicate_header",
                     f"Duplicates {first}1 after ID normalization", severity="error")
        else:
            header_columns[key] = column
        headers[column] = (raw, key)
    if not headers:
        qc_issue(issues, source, sheet.title, 1, 0, "missing_headers", "No named assay columns",
                 severity="error")

    scores = {}
    score_locations = {}
    host_ids = set()
    ignored_cells = 0
    rows_without_ids = []
    for index, row in enumerate(rows, start=2):
        if not row or all(blank(value) for value in row):
            continue
        missing_host = blank(row[0])
        if missing_host:
            if any(column < len(row) and not blank(row[column]) for column in headers):
                rows_without_ids.append(index)
        else:
            raw_host, host = normalize_id(row[0])
            host_ids.add(host)
        for column, value in enumerate(row[1:], start=1):
            if blank(value):
                continue
            if column not in headers:
                ignored_cells += 1
                qc_issue(issues, source, sheet.title, index, column, "unnamed_column",
                         "Populated cell under a blank header")
                continue
            if missing_host:
                qc_issue(issues, source, sheet.title, index, column, "missing_host_id",
                         f"Observation has no host ID in A{index}")
                continue
            raw_phage, phage = headers[column]
            score = str(value).strip()
            if not re.fullmatch(r"[0-9](?:\.0+)?", score) or int(float(score)) not in SCORES[sheet.title]:
                qc_issue(issues, source, sheet.title, index, column, "invalid_score",
                         "Value outside the recorded score scale", severity="error")
                continue
            key = (host, phage)
            if key in scores:
                qc_issue(issues, source, sheet.title, index, column, "duplicate_observation",
                         f"Duplicates observation at {score_locations[key]}", severity="error")
                continue
            score_locations[key] = f"{get_column_letter(column + 1)}{index}"
            scores[key] = (raw_host, raw_phage, int(float(score)))
    return scores, host_ids, header_columns, ignored_cells, rows_without_ids


def read_assays(paths, issues):
    records = []
    ids = {"host": set(), "phage": set()}
    audit = []
    for path in paths:
        workbook = load_workbook(path, read_only=True, data_only=True)
        try:
            if missing := SCORES.keys() - set(workbook.sheetnames):
                for name in sorted(missing):
                    issues.append((path.name, name, "", "error", "missing_sheet", "Required worksheet is absent"))
                continue
            category, binary = (read_sheet(workbook[name], path.name, issues) for name in SCORES)
        finally:
            workbook.close()
        for _, hosts, phages, _, _ in (category, binary):
            ids["host"].update(hosts)
            ids["phage"].update(phages)
        category_scores, _, category_ids, category_ignored, category_orphans = category
        binary_scores, _, binary_ids, binary_ignored, binary_orphans = binary
        for sheet, present, other in (("category", category_ids, binary_ids), ("binary", binary_ids, category_ids)):
            for name in sorted(present.keys() - other.keys()):
                qc_issue(issues, path.name, sheet, 1, present[name], "header_mismatch",
                         "ID absent from the other worksheet header")
        audit.append((path.name, category_ignored, binary_ignored, category_ids.keys() ^ binary_ids.keys(),
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
    mappings = defaultdict(lambda: defaultdict(list))
    if aliases_path:
        with aliases_path.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            fields = tuple(reader.fieldnames or ())
            if fields not in (ALIAS_FIELDS, (*ALIAS_FIELDS, "review_status")):
                raise ValueError(f"{aliases_path} must use these columns: {', '.join((*ALIAS_FIELDS, 'review_status'))}")
            seen = set()
            for row in reader:
                role, source, target, evidence = ((row[key] or "").strip() for key in ALIAS_FIELDS)
                if role == "prophage":
                    continue
                status = (row.get("review_status", "confirmed") or "").strip()
                key = (role, source, target)
                if (None in row or role not in roots or not source or not target or status not in REVIEW_STATES
                        or status == "confirmed" and not evidence or key in seen):
                    raise ValueError(f"Invalid or duplicate alias at {aliases_path}:{reader.line_num}")
                seen.add(key)
                mappings[role][source].append((target, evidence, status))

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
            aliases = mappings[role][name]
            confirmed = {target: evidence for target, evidence, status in aliases if status == "confirmed"}
            pending = sorted(target for target, _, status in aliases if status == "pending")
            if name in files:
                confirmed.setdefault(name, "Exact ID")
            if len(confirmed) > 1:
                detail = "Competing mappings: " + ", ".join(sorted(confirmed))
                entries.append((role, name, "", "", "conflict", detail))
                continue
            if not confirmed and pending:
                entries.append((role, name, "", "", "pending_review", "Candidates: " + ", ".join(pending)))
                continue
            target, evidence = next(iter(confirmed.items()), (name, ""))
            if target in files:
                entries.append((role, name, target, str(files[target]), "matched", evidence))
                used.add(target)
            else:
                entries.append((role, name, target, "", "genome_missing", evidence))
        for name in sorted(files.keys() - used):
            entries.append((role, "", name, str(files[name]), "label_missing", ""))
    return entries


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(fields)
        writer.writerows(rows)


def inventory_text(records, coverage, audit, issues):
    matched = {role: {row[1] for row in coverage if row[0] == role and row[4] == "matched"}
               for role in ("host", "phage")}
    covered = sum(row[2] in matched["host"] and row[3] in matched["phage"] for row in records)
    lines = ["# Assay data inventory", "", f"- Observed pairs per source workbook, summed: {len(records)}",
             f"- Distinct normalized pairs across workbooks: {len({row[2:4] for row in records})}",
             f"- Observations with confirmed local IDs on both sides: {covered}",
             f"- Observations with unresolved local IDs: {len(records) - covered}",
             "- Binary positive counts use the workbook's recorded value of 1.", ""]
    coverage_counts = Counter(row[4] for row in coverage)
    lines.append("- Crosswalk statuses: " + ", ".join(f"{status}: {count}" for status, count in sorted(coverage_counts.items())))
    lines.append(f"- Workbook QC entries: {len(issues)}")
    for name, column in (("Category", 4), ("Binary", 5)):
        counts = Counter(row[column] for row in records)
        values = ", ".join(f"{key}: {counts[key]}" for key in sorted(counts.keys() - {None}))
        lines.extend((f"- {name} counts: {values or 'none'} · blank: {counts[None]}",))
    for role, index in (("host", 2), ("phage", 3)):
        totals = Counter(row[index] for row in records if row[5] is not None)
        positives = Counter(row[index] for row in records if row[5] == 1)
        lines.extend(("", f"## Recorded binary positives by {role}", ""))
        lines.extend(f"- `{name}`: {positives[name]} / {totals[name]}" for name in sorted(totals))
        unresolved = [row[1] for row in coverage if row[0] == role and row[1] and row[4] != "matched"]
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
    parser.add_argument("--qc", type=Path, default=Path("reports/assay_qc.csv"))
    parser.add_argument("--allow-unresolved", action="store_true", help="Return success with unresolved IDs")
    args = parser.parse_args(argv)
    try:
        if len({path.name for path in args.workbooks}) != len(args.workbooks):
            raise ValueError("Workbook basenames must be distinct for provenance")
        inputs = {path.resolve() for path in args.workbooks}
        if args.aliases:
            inputs.add(args.aliases.resolve())
        outputs = {path.resolve() for path in (args.interactions, args.crosswalk, args.report, args.qc)}
        if len(outputs) != 4 or inputs & outputs:
            raise ValueError("Output paths must be distinct and separate from source files")
        issues = []
        records, ids, audit = read_assays(args.workbooks, issues)
        write_csv(args.qc, QC_FIELDS, issues)
        if any(issue[3] == "error" for issue in issues):
            parser.exit(2, f"Workbook QC found blocking errors. Review {args.qc}.\n")
        coverage = file_coverage(ids, {"host": args.host_dir, "phage": args.phage_dir}, args.aliases)
        write_csv(args.interactions, FIELDS, records)
        write_csv(args.crosswalk, ("role", "label_id", "genome_id", "path", "status", "evidence"), coverage)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(inventory_text(records, coverage, audit, issues), encoding="utf-8")
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(2, f"Assay inventory error: {exc}\n")
    unresolved = sum(row[4] != "matched" for row in coverage)
    print(f"Wrote {len(records)} observations and {len(coverage)} crosswalk entries. Unresolved IDs: {unresolved}.")
    if unresolved and not args.allow_unresolved:
        parser.exit(2, "Crosswalk has unresolved IDs. Review the generated report.\n")


if __name__ == "__main__":
    main()
