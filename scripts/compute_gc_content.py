#!/usr/bin/env python3
"""
Compute GC content for all genome FASTA files in a directory and write results to CSV.
Usage:
    python scripts/compute_gc_content.py -i data/E_coli_genomes/Genomes_ID -o data/processed/genomic_features/gc_content.csv
"""
import os
import csv
import argparse
from Bio import SeqIO

def calc_gc_content(seq):
    """Calculate GC percentage of a sequence."""
    seq_str = str(seq).upper()
    gc_count = seq_str.count('G') + seq_str.count('C')
    return (gc_count / len(seq_str) * 100) if len(seq_str) > 0 else 0

def main():
    parser = argparse.ArgumentParser(description="Compute GC content for genomes")
    parser.add_argument('-i', '--input', required=True,
                        help='Directory containing genome FASTA files (.fna/.fa/.fasta)')
    parser.add_argument('-o', '--output', required=True,
                        help='Output CSV file for GC content results')
    args = parser.parse_args()

    # Check input directory
    if not os.path.isdir(args.input):
        parser.error(f"Input directory does not exist: {args.input}")

    # Ensure output directory exists
    out_dir = os.path.dirname(args.output)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    # Prepare CSV
    with open(args.output, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['genome_id', 'gc_content'])

        # Process each FASTA file
        for fname in os.listdir(args.input):
            if not fname.lower().endswith(('.fna', '.fa', '.fasta')):
                continue
            fpath = os.path.join(args.input, fname)
            # Concatenate all records into one sequence (or take the first record)
            total_gc = []
            for record in SeqIO.parse(fpath, 'fasta'):
                gc = calc_gc_content(record.seq)
                total_gc.append(gc)
            if total_gc:
                # average GC across records
                avg_gc = sum(total_gc) / len(total_gc)
                sample_id = os.path.splitext(fname)[0]
                writer.writerow([sample_id, f"{avg_gc:.2f}"])
                print(f"{sample_id}: GC content {avg_gc:.2f}%")
            else:
                print(f"No sequences found in {fname}")

if __name__ == '__main__':
    main()
