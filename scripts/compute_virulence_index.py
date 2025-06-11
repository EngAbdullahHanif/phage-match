#!/usr/bin/env python3
"""
Compute virulence index placeholder from binary infection data and combine with inhibition efficiencies.

Usage:
  python scripts/compute_virulence_index.py \
    -b data/metadata/sst_e_coli_phages.xlsx -s binary \
    -i data/processed/phenotypes/inhibition_efficiency.csv \
    -o data/processed/phenotypes/phenotypic_metadata.csv
"""
import os
import argparse
import pandas as pd

def load_matrix(path, sheet=None):
    if path.lower().endswith(('.xls', '.xlsx')):
        return pd.read_excel(path, sheet_name=sheet, index_col=0)
    else:
        return pd.read_csv(path, index_col=0)


def main():
    p = argparse.ArgumentParser(description="Generate virulence index and combine phenotype matrices")
    p.add_argument('-b', '--binary', required=True,
                   help='Binary infection matrix (Excel or CSV) with 0/1 values')
    p.add_argument('-s', '--sheet', default=None,
                   help='Sheet name for Excel input (default: first sheet)')
    p.add_argument('-i', '--inhibition', required=True,
                   help='CSV of normalized inhibition efficiencies')
    p.add_argument('-o', '--output', required=True,
                   help='Output CSV for combined phenotypic metadata')
    args = p.parse_args()

    # Load binary matrix (0/1)
    bin_df = load_matrix(args.binary, sheet=args.sheet)
    # Map to placeholder virulence index
    vir_df = bin_df.replace({1: 1.0, 0: 0.2})

    # Load inhibition efficiency matrix
    inh_df = pd.read_csv(args.inhibition, index_col=0)

    # Melt both to long format
    inh_long = inh_df.reset_index().melt(id_vars=inh_df.index.name or 'index',
                                         var_name='phage', value_name='inhibition_efficiency')
    inh_long = inh_long.rename(columns={inh_df.index.name or 'index': 'host_id'})

    vir_long = vir_df.reset_index().melt(id_vars=vir_df.index.name or 'index',
                                         var_name='phage', value_name='virulence_index')
    vir_long = vir_long.rename(columns={vir_df.index.name or 'index': 'host_id'})

    # Merge on host_id + phage
    merged = pd.merge(inh_long, vir_long, on=['host_id', 'phage'], how='outer')

    # Ensure output dir exists
    out_dir = os.path.dirname(args.output)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    merged.to_csv(args.output, index=False)
    print(f"Wrote combined phenotypic metadata to {args.output}")

if __name__ == '__main__':
    main()
