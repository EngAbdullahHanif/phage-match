import csv

import pytest
from openpyxl import Workbook

from scripts.build_interactions import file_coverage, main


def table(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def test_workbooks_provenance_and_strict_file_coverage(tmp_path):
    first = Workbook()
    first.active.title = "category"
    first.active.append(["host", "sample-a", "sample-b"])
    first.active.append(["65.0", 0, 2])
    first.active.append(["P2.2", None, 3])
    second = first.create_sheet("binary")
    second.append(["host", "sample-b", "sample-a"])
    second.append([65, 1, 0, "unconfirmed"])
    second.append([None, 11, 9])
    book_a = tmp_path / "assay a.xlsx"
    first.save(book_a)

    other = Workbook()
    other.active.title = "category"
    other.active.append(["host", "sample-a"])
    other.create_sheet("binary").append(["host", "sample-a"])
    other["binary"].append(["22-18", 1])
    book_b = tmp_path / "assay b.xlsx"
    other.save(book_b)

    hosts = tmp_path / "hosts"
    hosts.mkdir()
    (hosts / "65.fasta").touch()
    phages = tmp_path / "phages"
    phages.mkdir()
    (phages / "renamed.fna").touch()
    (phages / "unlabeled.fna").touch()
    aliases = tmp_path / "aliases.tsv"
    aliases.write_text("role\tsource_id\ttarget_id\tevidence\nphage\tsample-a\trenamed\tfixture record\n")
    output, crosswalk, report, qc = (tmp_path / name for name in ("assays.csv", "ids.csv", "inventory.md", "qc.csv"))
    args = [str(book_a), str(book_b), "--host-dir", str(hosts), "--phage-dir", str(phages),
            "--aliases", str(aliases), "--interactions", str(output), "--crosswalk", str(crosswalk),
            "--report", str(report), "--qc", str(qc)]
    with pytest.raises(SystemExit) as error:
        main(args)
    assert error.value.code == 2
    rows = table(output)
    assert len(rows) == 4
    assert rows[0]["host_id_raw"] == "65.0"
    assert rows[0]["host_id"] == "65"
    assert rows[0]["category"] == rows[0]["binary"] == "0"
    assert rows[0]["source_sheet"] == "category,binary"
    assert rows[-1]["host_id"] == "22-18" and rows[-1]["category"] == ""
    assert {row["status"] for row in table(crosswalk)} == {"matched", "genome_missing", "label_missing"}
    assert "binary [3]" in report.read_text()
    assert "on both sides: 1" in report.read_text()
    assert {(row["cell"], row["code"]) for row in table(qc)} == {
        ("D2", "unnamed_column"), ("B3", "missing_host_id"), ("C3", "missing_host_id"),
    }
    main([*args, "--allow-unresolved"])



def test_blocking_workbook_issues_report_cells_without_replacing_exports(tmp_path):
    workbook = Workbook()
    category = workbook.active
    category.title = "category"
    category.append(["host", "a", "b"])
    category.append(["first", 1, 9])
    category.append(["first", 2, None])
    binary = workbook.create_sheet("binary")
    binary.append(["host", "a"])
    binary.append(["first", 0])
    book = tmp_path / "synthetic.xlsx"
    workbook.save(book)
    qc = tmp_path / "qc.csv"
    output = tmp_path / "assays.csv"
    output.write_text("prior report\n")
    with pytest.raises(SystemExit) as error:
        main([str(book), "--qc", str(qc), "--interactions", str(output), "--allow-unresolved"])
    assert error.value.code == 2
    assert output.read_text() == "prior report\n"
    assert {(row["cell"], row["code"], row["severity"]) for row in table(qc)} == {
        ("C1", "header_mismatch", "review"), ("C2", "invalid_score", "error"),
        ("B3", "duplicate_observation", "error"),
    }
    assert next(row for row in table(qc) if row["cell"] == "B3")["detail"].endswith("B2")


def test_reviewed_aliases_distinguish_confirmed_pending_conflicts_and_missing(tmp_path):
    for stem in ("exact", "target", "other"):
        (tmp_path / f"{stem}.fna").touch()
    aliases = tmp_path / "aliases.tsv"
    aliases.write_text(
        "role\tsource_id\ttarget_id\tevidence\treview_status\n"
        "host\texact\tother\tregistry contradiction\tconfirmed\n"
        "host\tconfirmed\ttarget\tregistry entry\tconfirmed\n"
        "host\tpending\tother\t\tpending\n"
        "host\trejected\tother\tregistry contradicts candidate\trejected\n"
    )
    coverage = file_coverage({"host": {"exact", "confirmed", "pending", "rejected"}}, {"host": tmp_path}, aliases)
    assert {row[1]: row[4] for row in coverage if row[1]} == {
        "confirmed": "matched", "exact": "conflict", "pending": "pending_review", "rejected": "genome_missing",
    }
    aliases.write_text(aliases.read_text().replace("registry entry", ""))
    with pytest.raises(ValueError, match="Invalid or duplicate alias"):
        file_coverage({"host": {"confirmed"}}, {"host": tmp_path}, aliases)
