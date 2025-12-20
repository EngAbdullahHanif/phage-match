#!/usr/bin/env python3

import os
import argparse
import subprocess

def main():
    p = argparse.ArgumentParser(description="Detect tRNAs with Aragorn")
    p.add_argument("-i","--input", required=True,
                   help="Base dir of Prokka annotation subdirs")
    p.add_argument("-o","--output", required=True,
                   help="Output dir for tRNA reports")
    p.add_argument("-a","--aragorn", default="aragorn",
                   help="Path to aragorn binary")
    args = p.parse_args()

    os.makedirs(args.output, exist_ok=True)

    for sub in os.listdir(args.input):
        anno = os.path.join(args.input, sub)
        if not os.path.isdir(anno):
            continue
        phage = sub.replace("_annotation","")
        # look for genome FASTA (.fna/.fa/.fasta) named after phage
        genome = None
        for ext in (".fna", ".fa", ".fasta"):
            candidate = os.path.join(anno, phage + ext)
            if os.path.isfile(candidate):
                genome = candidate
                break
        if genome is None:
            print(f"[WARN] no genome FASTA for {phage}, skipping")
            continue

        out = os.path.join(args.output, f"{phage}_tRNA.out")
        cmd = [ args.aragorn, "-t", "-gc11", "-o", out, genome ]
        print("Running:", " ".join(cmd))
        subprocess.run(cmd, check=True)

    print("tRNA detection complete. Results in", args.output)

if __name__=="__main__":
    main()