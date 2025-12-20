#!/usr/bin/env python3
"""
Resume InterProScan for phage genomes after HHsearch failures or interruptions.

Usage:
  python scripts/resume_interproscan.py \
    -i data/processed/annotations/phage_genomes \
    -o data/processed/annotations/rbp_predictions \
    -p /path/to/interproscan.sh

This script will skip genomes without HHsearch results and will only run
InterProScan for those genomes where HHsearch output exists but InterProScan
results are missing.
"""
import os
import argparse
import subprocess
import shutil


def main():
    parser = argparse.ArgumentParser(
        description='Resume InterProScan after HHsearch')
    parser.add_argument('-i', '--input', required=True,
                        help='Directory of Prokka annotation subdirs')
    parser.add_argument('-o', '--output', required=True,
                        help='RBP predictions output directory')
    parser.add_argument('-p', '--interpro', default='interproscan.sh',
                        help='Path to InterProScan script')
    parser.add_argument('--appl', default='Pfam,TIGRFAM',
                        help='Comma-separated list of InterProScan apps to run (default: Pfam,TIGRFAM; skipping SMART & ProSiteProfiles)')
    args = parser.parse_args()

    hh_dir = os.path.join(args.output, 'hhsearch')
    # print("hh_dir: ", hh_dir)
    ip_dir = os.path.join(args.output, 'interpro')
    os.makedirs(ip_dir, exist_ok=True)

    for sub in os.listdir(args.input):
        anno_dir = os.path.join(args.input, sub)
        if not os.path.isdir(anno_dir):
            continue
        phage_id = sub.replace('_annotation', '')
        faa = os.path.join(anno_dir, f"{phage_id}.faa")
        if not os.path.isfile(faa):
            continue

        # prepare InterProScan output path
        ip_file = os.path.join(ip_dir, f"{phage_id}_interpro.tsv")
        # skip if already done
        if os.path.isfile(ip_file):
            print(f"[SKIP] InterProScan already done for {phage_id}")
            continue
        # warn if no HHsearch outputs found, but proceed
        hh_matches = [f for f in os.listdir(hh_dir) if f.startswith(f"{phage_id}_") and f.endswith("_hhsearch.txt")]
        if not hh_matches:
            print(f"[WARN] No HHsearch outputs for {phage_id}, but proceeding with InterProScan")
        # run InterProScan for this phage
        # build InterProScan command
        cmd = [args.interpro, '-i', faa, '-f', 'tsv', '-o', ip_file]
        # filter requested InterProScan apps based on available executables
        selected = []
        for app in args.appl.split(',') if args.appl else []:
            app = app.strip()
            if app == 'ProSiteProfiles':
                # check for runprosite.py
                if not os.path.isfile(os.path.join(os.path.dirname(args.interpro), 'bin/prosite/runprosite.py')):
                    print(f"[WARN] ProSiteProfiles script missing, skipping {app}")
                    continue
            if app == 'SMART':
                # SMART uses hmmpfam
                if not shutil.which('hmmpfam'):
                    print(f"[WARN] SMART hmmpfam not in PATH, skipping {app}")
                    continue
            selected.append(app)
        if selected:
            cmd.extend(['-appl', ','.join(selected)])
        print(f"[RUN] InterProScan for {phage_id}")
        subprocess.run(cmd, check=True)

    print("Resume InterProScan tasks complete.")


if __name__ == '__main__':
    main()
