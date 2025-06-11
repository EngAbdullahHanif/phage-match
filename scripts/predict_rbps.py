#!/Users/mac/miniconda3/envs/prokka_env/bin/python

"""
Predict receptor-binding proteins (RBPs) using HHsearch and InterProScan.

Usage:
  python scripts/predict_rbps.py \
    -i data/processed/annotations/phage_genomes \
    -o data/processed/annotations/rbp_predictions \
    -d /db/pdb70 \
    -p /path/to/interproscan.sh

Outputs:
  - HHsearch outputs (*.txt) in output/hhsearch/
  - InterProScan TSV outputs (*.tsv) in output/interpro/
"""
import os
import argparse
import subprocess
from Bio import SeqIO

def main():
    parser = argparse.ArgumentParser(description='Predict RBPs via HHsearch & InterProScan')
    parser.add_argument('-i', '--input', required=True,
                        help='Directory of Prokka annotation subdirs (e.g., phageID_annotation)')
    parser.add_argument('-o', '--output', required=True,
                        help='Output directory for RBP predictions')
    parser.add_argument('-d', '--hhdb', default='db/pdb70',
                        help='Path prefix to HHsearch database (e.g., db/pdb70)')
    parser.add_argument('-p', '--interpro', default='interproscan.sh',
                        help='Path to InterProScan script')
    args = parser.parse_args()

    # prepare output dirs
    hh_dir = os.path.join(args.output, 'hhsearch')
    ip_dir = os.path.join(args.output, 'interpro')
    os.makedirs(hh_dir, exist_ok=True)
    os.makedirs(ip_dir, exist_ok=True)

    # iterate each annotation subdir
    for sub in os.listdir(args.input):
        anno_dir = os.path.join(args.input, sub)
        if not os.path.isdir(anno_dir):
            continue
        phage_id = sub.replace('_annotation', '')
        faa = os.path.join(anno_dir, f"{phage_id}.faa")
        if not os.path.isfile(faa):
            print(f"[WARN] No .faa for {phage_id}, skipping")
            continue

        # --- Insert per-sequence split + reformat + hhmake + hhsearch loop ---
        for rec in SeqIO.parse(faa, "fasta"):
            seq_id = rec.id
            one_faa = os.path.join(anno_dir, f"{seq_id}.faa")
            with open(one_faa, "w") as fh:
                SeqIO.write(rec, fh, "fasta")

            # convert to A3M, build HMM, run HHsearch per protein
            a3m = one_faa.replace(".faa", ".a3m")
            subprocess.run(["reformat.pl", "fas", "a3m", one_faa, a3m], check=True)
            hhm = a3m.replace(".a3m", ".hhm")
            subprocess.run(["hhmake", "-i", a3m, "-o", hhm], check=True)

            out_hh = os.path.join(hh_dir, f"{seq_id}_hhsearch.txt")
            subprocess.run(["hhsearch", "-i", hhm, "-d", args.hhdb, "-o", out_hh], check=True)
#######

        # Convert protein FASTA to A3M format for HHsearch
        a3m = os.path.join(anno_dir, f"{phage_id}.a3m")
        print(f"Preparing A3M database for {phage_id}")
        subprocess.run([
            'ffindex_from_fasta',
            '-s', a3m + '.ffdata',
            a3m + '.ffindex',
            faa
        ], check=True)

        # Run HHsearch on prepared A3M
        out_hh = os.path.join(hh_dir, f"{phage_id}_hhsearch.txt")
        cmd_hh = [
            'hhsearch',
            '-i', a3m,
            '-d', args.hhdb,
            '-o', out_hh,
            '-cpu', '4'
        ]
        print(f"Running HHsearch for {phage_id}")
        subprocess.run(cmd_hh, check=True)

        # InterProScan
        out_ip = os.path.join(ip_dir, f"{phage_id}_interpro.tsv")
        cmd_ip = [args.interpro, '-i', faa, '-f', 'tsv', '-o', out_ip]
        print(f"Running InterProScan for {phage_id}")
        subprocess.run(cmd_ip, check=True)

    print(f"RBP prediction completed. Results in {args.output}")

if __name__ == '__main__':
    main()
