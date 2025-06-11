import os
import argparse
import subprocess
import shutil


def annotate_phage_genomes(input_dir, output_dir):
    for filename in os.listdir(input_dir):
        if filename.endswith(".fasta") or filename.endswith(".fa") or filename.endswith(".fna"):
            phage_id = os.path.splitext(filename)[0]
            input_path = os.path.join(input_dir, filename)
            
            # Run Prokka
            prokka_outdir = os.path.join(output_dir, f"{phage_id}_annotation")
            prokka_prefix = phage_id
            print(f"Running Prokka for {phage_id}")
            subprocess.run([
                "prokka",
                "--outdir", prokka_outdir,
                "--prefix", prokka_prefix,
                "--force",
                "--addgenes",        # add /gene qualifiers for NCBI compliance
                "--compliant",       # ensure NCBI-compliant output
                "--kingdom", "Viruses",  # use virus-specific databases
                "--mincontiglen", "100", # ignore small contigs <100 bp
                input_path
            ], check=True)

            # Copy .faa file to standardized location and name
            original_faa = os.path.join(prokka_outdir, f"{phage_id}.faa")
            standard_faa_dir = os.path.join(output_dir, f"{phage_id}_proteins_annotation")
            os.makedirs(standard_faa_dir, exist_ok=True)
            standard_faa_path = os.path.join(standard_faa_dir, f"{phage_id}_proteins_proteins.faa")
            shutil.copyfile(original_faa, standard_faa_path)
            print(f"Saved protein FASTA: {standard_faa_path}")

def main():
    parser = argparse.ArgumentParser(description="Annotate phage genomes using Prokka.")
    parser.add_argument("-i", "--input", required=True, help="Directory with phage genome FASTA files")
    parser.add_argument("-o", "--output", required=True, help="Directory to store Prokka annotations and protein FASTAs")
    args = parser.parse_args()

    annotate_phage_genomes(args.input, args.output)

if __name__ == "__main__":
    main()
