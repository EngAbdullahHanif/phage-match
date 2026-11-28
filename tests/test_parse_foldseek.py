import math
import shutil
import subprocess

import pytest

from scripts.parse_foldseek import COLUMNS, write_structural_similarity


def test_empty_foldseek_table_has_header(tmp_path):
    source = tmp_path / "empty.m8"
    destination = tmp_path / "alignments.tsv"
    source.touch()
    write_structural_similarity(source, destination)
    assert destination.read_text() == "\t".join(COLUMNS) + "\n"


def test_malformed_foldseek_row_preserves_previous_output(tmp_path):
    source = tmp_path / "malformed.m8"
    destination = tmp_path / "alignments.tsv"
    valid_row = "toy-q\ttoy-t\t1.0\t40\t0\t0\t1\t40\t1\t40\t0.001\t70"
    source.write_text(valid_row + "\ntoo\tshort\n")
    destination.write_text("previous export\n")
    with pytest.raises(ValueError, match=r"malformed\.m8:2 expected 12 Foldseek columns"):
        write_structural_similarity(source, destination)
    assert destination.read_text() == "previous export\n"
    source.write_text(valid_row + "\n")
    write_structural_similarity(source, destination)
    assert destination.read_text().splitlines() == ["\t".join(COLUMNS), valid_row]


@pytest.mark.skipif(shutil.which("foldseek") is None, reason="Foldseek executable required for synthetic smoke test")
def test_foldseek_easy_search_synthetic_helix(tmp_path):
    model = tmp_path / "synthetic_helix.pdb"
    atoms = []
    for residue in range(1, 61):
        theta = math.radians(100 * residue)
        x, y, z = 2.3 * math.cos(theta), 2.3 * math.sin(theta), 1.5 * residue
        atoms.append(f"ATOM  {residue:5d}  CA  ALA A{residue:4d}    "
                     f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00 20.00           C\n")
    model.write_text("".join(atoms) + "TER\nEND\n")
    raw = tmp_path / "synthetic.m8"
    subprocess.run(["foldseek", "easy-search", str(model), str(model), str(raw), str(tmp_path / "work"),
                    "--threads", "1", "--exhaustive-search", "1"], check=True, capture_output=True, text=True)
    destination = tmp_path / "alignments.tsv"
    write_structural_similarity(raw, destination)
    header, *rows = destination.read_text().splitlines()
    assert header.split("\t") == list(COLUMNS)
    assert rows
