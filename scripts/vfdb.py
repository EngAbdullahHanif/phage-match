#!/usr/bin/env python3

"""
Custom VFDB annotation wrapper using abricate.

Scans all FASTA files in the input directory against the VFDB database
and writes per-genome TSV outputs to the output directory.
"""
import os
import argparse
import subprocess


def main():
    parser = argparse.ArgumentParser(description="Run abricate VFDB on a directory of genomes")
    parser.add_argument('-i', '--input', required=True,
                        help='Directory containing genome FASTA files (.fna/.fa/.fasta)')
    parser.add_argument('-o', '--output', required=True,
                        help='Output directory for per-genome VFDB annotations')
    parser.add_argument('--db', default='vfdb',
                        help='Name of abricate database (default: vfdb)')
    args = parser.parse_args()

    # Ensure input exists
    if not os.path.isdir(args.input):
        raise FileNotFoundError(f"Input directory not found: {args.input}")
    os.makedirs(args.output, exist_ok=True)

    # Find all FASTA files
    fasta_exts = ('.fna', '.fa', '.fasta')
    fastas = [f for f in os.listdir(args.input) if f.lower().endswith(fasta_exts)]
    if not fastas:
        print(f"No FASTA files found in {args.input}")
        return

    # Run abricate for each FASTA
    for fasta in fastas:
        infile = os.path.join(args.input, fasta)
        base = os.path.splitext(fasta)[0]
        outfile = os.path.join(args.output, f"{base}_vfdb.tsv")
        cmd = ['abricate', '--db', args.db, infile]
        print(f"Processing {fasta} -> {outfile}")
        with open(outfile, 'w') as out:
            subprocess.run(cmd, stdout=out, check=True)

    print(f"Done. VFDB annotations written to: {args.output}")


if __name__ == '__main__':
    main()
