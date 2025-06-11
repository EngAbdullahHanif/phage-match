#!/usr/bin/env python3
"""
Plot clustered heatmap of phage-host interaction strengths.

Usage:
  python scripts/plot_interaction_heatmap.py \
    -i data/processed/phenotypes/inhibition_efficiency.csv \
    -o data/processed/phenotypes/interaction_heatmap.png
"""
import argparse
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def main():
    p = argparse.ArgumentParser(description='Clustered heatmap of interaction matrix')
    p.add_argument('-i','--input', required=True, help='CSV of normalized interaction matrix')
    p.add_argument('-o','--output', required=True, help='Output PNG file path')
    args = p.parse_args()

    # Load interaction matrix
    df = pd.read_csv(args.input, index_col=0)

    # Plot clustermap
    sns.clustermap(df,
                   row_cluster=True,
                   col_cluster=True,
                   cmap='viridis',
                   figsize=(10, 8))
    plt.title('Phage-Host Interaction Strengths (Normalized 0-1)')

    # Ensure output directory
    out_dir = os.path.dirname(args.output)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    plt.savefig(args.output, dpi=300, bbox_inches='tight')
    print(f'Heatmap saved to {args.output}')

if __name__ == '__main__':
    main()
