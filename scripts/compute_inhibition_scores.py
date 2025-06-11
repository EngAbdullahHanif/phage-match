#!/usr/bin/env python3
"""
Compute normalized inhibition efficiency scores from spot-test category data.
Usage:
  python scripts/compute_inhibition_scores.py \
    -i data/metadata/SST_ E. coli and Salmonella phages.xlsx \
    -s category \
    -o data/processed/phenotypes/inhibition_efficiency.csv
"""
import os
import argparse
import pandas as pd

def main():
    p = argparse.ArgumentParser(description="Normalize spot-test category (0–3) to 0–1")
    p.add_argument('-i','--input', required=True,
                   help='Excel file with spot-test categories')
    p.add_argument('-s','--sheet', default='category',
                   help='Sheet name (default: category)')
    p.add_argument('-o','--output', required=True,
                   help='Output CSV for normalized interaction matrix')
    args = p.parse_args()

    # read data
    df = pd.read_excel(args.input, sheet_name=args.sheet)
    if df.shape[1] < 2:
        raise ValueError("Expected at least two columns: ID + phage columns")
    # first column = host IDs
    host_ids = df.iloc[:, 0]
    mat = df.iloc[:, 1:].to_numpy(dtype=float)

    # normalize 0–3 → 0–1
    norm = mat / 3.0

    # rebuild DataFrame
    out_df = pd.DataFrame(norm,
                          index=host_ids,
                          columns=df.columns[1:])

    # ensure output path exists
    out_dir = os.path.dirname(args.output)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    out_df.to_csv(args.output, index_label='host_id')
    print(f"Wrote normalized inhibition matrix to {args.output}")

if __name__ == '__main__':
    main()
