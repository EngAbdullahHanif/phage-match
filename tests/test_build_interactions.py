import csv

import pytest
from openpyxl import Workbook

from scripts.build_interactions import main


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
    output, crosswalk, report = (tmp_path / name for name in ("assays.csv", "ids.csv", "inventory.md"))
    args = [str(book_a), str(book_b), "--host-dir", str(hosts), "--phage-dir", str(phages),
            "--aliases", str(aliases), "--interactions", str(output), "--crosswalk", str(crosswalk),
            "--report", str(report)]
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
    main([*args, "--allow-unresolved"])
