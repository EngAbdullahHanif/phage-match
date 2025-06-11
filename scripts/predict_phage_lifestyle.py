#!/usr/bin/env python3
"""
Predict phage lifestyle (lytic vs temperate) using PHACTS on local genome FASTAs.

Usage:
  pip install phacts prodigal
  python scripts/predict_phage_lifestyle.py \
    -i data/raw/phage_genomes \
    -o data/processed/phenotypes/lifestyle

Outputs:
  - Text output per phage from PHACTS in output folder
  - CSV summary 'lifestyle_summary.csv' with columns: phage,lifestyle,probability,stdev
"""
import os
import argparse
import subprocess
import pandas as pd

def main():
    p = argparse.ArgumentParser(description="Predict phage lifestyle with PHACTS")
    p.add_argument('-i', '--input', required=True,
                   help='Directory of phage genome FASTA files (nucleotide)')
    p.add_argument('-o', '--output', required=True,
                   help='Output directory for lifestyle predictions')
    args = p.parse_args()

    # Ensure output dir
    os.makedirs(args.output, exist_ok=True)
    protein_dir = os.path.join(args.output, "proteins")
    os.makedirs(protein_dir, exist_ok=True)

    print(f"Input directory: {args.input}")
    print(f"Directory exists: {os.path.exists(args.input)}")
    print(f"Files in directory: {os.listdir(args.input)}")

    # Find all FASTA files
    fasta_exts = ('.fna', '.fa', '.fasta', '.FNA', '.FA', '.FASTA')
    for f in os.listdir(args.input):
        print(f"{f} - readable: {os.access(os.path.join(args.input, f), os.R_OK)}")

    phages = [f for f in os.listdir(args.input) if f.lower().endswith(fasta_exts)]
    print(f"Found {len(phages)} phage files: {phages}")
    
    summary = []
    # Path to phacts.py in the virtual environment
    phacts_script = "/Users/mac/Documents/Development Projects/PhageMatch/env/bin/phacts.py"
    
    for fasta in phages:
        phage_id = os.path.splitext(fasta)[0]
        infile = os.path.join(args.input, fasta)
        protein_fasta = os.path.join(protein_dir, f"{phage_id}_proteins.fasta")
        outfile = os.path.join(args.output, f"{phage_id}_phacts.txt")

        print(f"Input file exists: {os.path.exists(infile)}")
        print(f"Output dir writable: {os.access(args.output, os.W_OK)}")

        # Run Prodigal to predict proteins
        print(f"Running Prodigal for {phage_id}...")
        try:
            subprocess.run(['prodigal', '-i', infile, '-a', protein_fasta], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running Prodigal for {phage_id}: {e}")
            summary.append({'phage': phage_id, 'lifestyle': 'error', 'probability': 0.0, 'stdev': 0.0})
            continue

        # Run PHACTS with protein FASTA
        cmd = ['python3', phacts_script, protein_fasta, '-o', outfile]
        print(f"Running PHACTS for {phage_id} with command: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(result.stdout)  # Debug PHACTS output
            print(result.stderr)  # Debug PHACTS errors
        except subprocess.CalledProcessError as e:
            print(f"Error running PHACTS for {phage_id}: {e}")
            print(f"STDERR: {e.stderr}")
            summary.append({'phage': phage_id, 'lifestyle': 'error', 'probability': 0.0, 'stdev': 0.0})
            continue

        # Parse PHACTS output (tabular format)
        try:
            with open(outfile) as f:
                lines = f.readlines()
            # Skip header line
            if len(lines) > 1:
                data = lines[1].strip().split('\t')
                lifestyle, prob, stdev = data[0], float(data[1]), float(data[2])
                summary.append({
                    'phage': phage_id,
                    'lifestyle': lifestyle,
                    'probability': prob,
                    'stdev': stdev
                })
            else:
                print(f"Empty output for {phage_id}: {outfile}")
                summary.append({'phage': phage_id, 'lifestyle': 'error', 'probability': 0.0, 'stdev': 0.0})
        except (FileNotFoundError, IndexError, ValueError):
            print(f"Invalid output for {phage_id}: {outfile}")
            summary.append({'phage': phage_id, 'lifestyle': 'error', 'probability': 0.0, 'stdev': 0.0})

    # Create summary CSV
    df = pd.DataFrame(summary)
    summary_csv = os.path.join(args.output, 'lifestyle_summary.csv')
    df.to_csv(summary_csv, index=False)
    print(f"Wrote lifestyle summary to {summary_csv}")

if __name__ == '__main__':
    main()