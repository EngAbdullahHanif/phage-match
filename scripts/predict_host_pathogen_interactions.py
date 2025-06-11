#!/usr/bin/env python3
"""
Predicts interactions between a single phage proteome and a single host proteome
using MMseqs2/Foldseek for structural prediction and search.
"""
import os
import argparse
import subprocess
import pandas as pd

def run_command(cmd, step_name=""):
    """Runs a command and handles errors."""
    print(f"--- Running: {step_name} ---")
    print(f"CMD: {' '.join(cmd)}\n")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Step '{step_name}' failed.")
        print(f"STDERR:\n{e.stderr}")
        raise

def main():
    p = argparse.ArgumentParser(description="Phage-Host PPI via MMseqs2/Foldseek")
    p.add_argument("--phage-faa", required=True, help="Path to the phage proteome FASTA file (from Prokka)")
    p.add_argument("--host-faa", required=True, help="Path to the host proteome FASTA file")
    p.add_argument("--out-dir", required=True, help="Output directory for all files for this run")
    args = p.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    # Define paths for intermediate and final files
    phage_struct_dir = os.path.join(args.out_dir, "phage_structures")
    host_struct_dir = os.path.join(args.out_dir, "host_structures")
    host_db_path = os.path.join(args.out_dir, "host_db")
    search_result_path = os.path.join(args.out_dir, "search_results.m8")
    final_output_path = os.path.join(args.out_dir, "interaction_predictions.tsv")

    try:
        # --- STEP 1: Predict 3D structures for phage and host proteins ---
        # CORRECTED: Use 'mmseqs easy-fold' for structure prediction
        run_command(['mmseqs', 'easy-fold', args.phage_faa, phage_struct_dir, os.path.join(args.out_dir, 'tmp_phage')], step_name="Phage Protein Folding")
        run_command(['mmseqs', 'easy-fold', args.host_faa, host_struct_dir, os.path.join(args.out_dir, 'tmp_host')], step_name="Host Protein Folding")

        # --- STEP 2: Create a database from the host structures ---
        run_command(['foldseek', 'createdb', host_struct_dir, host_db_path], step_name="Create Host Structure DB")

        # --- STEP 3: Search phage structures against the host database ---
        run_command(['foldseek', 'search', phage_struct_dir, host_db_path, search_result_path, os.path.join(args.out_dir, 'tmp_search')], step_name="Foldseek Search")
        
        # --- STEP 4: Parse the results and save to a clean TSV ---
        print("--- Parsing search results ---")
        col_names = ['phage_protein', 'host_protein', 'identity', 'alnlen', 'mismatch', 'gapopen', 'qstart', 'qend', 'tstart', 'tend', 'evalue', 'bits']
        results_df = pd.read_csv(search_result_path, sep='\t', header=None, names=col_names)
        
        results_df['phage_protein'] = results_df['phage_protein'].str.replace('.pdb', '', regex=False)
        results_df['host_protein'] = results_df['host_protein'].str.replace('.pdb', '', regex=False)

        significant_hits = results_df[results_df['evalue'] < 1e-3].sort_values(by='evalue')

        significant_hits.to_csv(final_output_path, sep='\t', index=False)
        print(f"\n[DONE] Found {len(significant_hits)} significant structural matches.")
        print(f"Final predictions written to: {final_output_path}")

    except (subprocess.CalledProcessError, FileNotFoundError, pd.errors.EmptyDataError) as e:
        print(f"\n[ERROR] The script failed to complete. Reason: {e}")

if __name__ == "__main__":
    main()