import pathlib, pandas as pd

configfile: "config.yaml"
PHASTER   = config["phaster_results"]
P_ANN     = config["phage_annotations"]
HHS_OUT   = config["hhsearch_out"]
UNI       = config["uniclust_db"]
PDB70     = config["pdb70_db"]
CACHE     = config["colabfold_cache"]
COLF_OUT  = config["colabfold_out"]
FSL_OUT   = config["foldseek_out"]
HOST_FAA  = config["host_faa"]

SAMPLES = [d.name for d in pathlib.Path(PHASTER).iterdir() if d.is_dir()]

rule all:
    input:
        expand(f"{FSL_OUT}/{s}/interaction_predictions.tsv", s=SAMPLES),
        "results/sourmash/k3_distance_matrix.csv"

rule prokka:
    input:
        fna = f"{PHASTER}/{s}/phage_regions.fna"
    output:
        dir = directory(f"{P_ANN}/{s}_annotation")
    params:
        prefix="{s}"
    conda: "envs/prokka.yml"
    shell:
        """
        prokka --force --kingdom Viruses \
          --outdir {output.dir} --prefix {params.prefix} {input.fna}
        """

rule hhblits:
    input:
        faa = f"{P_ANN}/{s}_annotation/{s}.faa"
    output:
        a3m = f"{HHS_OUT}/{s}/{s}.a3m"
    params:
        odir = f"{HHS_OUT}/{s}"
    conda: "envs/hhsuite.yml"
    shell:
        """
        mkdir -p {params.odir}
        hhblits -i {input.faa} -d {UNI} -oa3m {output.a3m}
        """

rule hhsearch:
    input:
        a3m = f"{HHS_OUT}/{s}/{s}.a3m"
    output:
        hhr = f"{HHS_OUT}/{s}/{s}.hhr"
    conda: "envs/hhsuite.yml"
    shell:
        "hhsearch -i {input.a3m} -d {PDB70} -o {output.hhr}"


rule sourmash_compare:
    input:
        phage_fnas = expand(f"{P_ANN}/{{s}}_annotation/{{s}}.fna", s=SAMPLES),
        host_fna   = config["host_fna"].replace(".faa", ".fna")
    output:
        matrix     = "results/sourmash/k3_distance_matrix.csv"
    params:
        phage_sig  = "results/sourmash/phage_k3.sig",
        host_sig   = "results/sourmash/host_k3.sig"
    conda: "envs/sourmash.yml"
    shell:
        r"""
        mkdir -p results/sourmash
        sourmash sketch dna -p k=3 {input.phage_fnas} -o {params.phage_sig}
        sourmash sketch dna -p k=3 {input.host_fna}   -o {params.host_sig}
        sourmash compare {params.phage_sig} {params.host_sig} \
          --csv {output.matrix}
        """

        
rule colabfold_phage:
    input:
        faa = f"{P_ANN}/{s}_annotation/{s}.faa"
    output:
        done = touch(f"{COLF_OUT}/phage_{s}/.done")
    params:
        outdir = f"{COLF_OUT}/phage_{s}"
    shell:
        """
        docker run --rm --gpus all \
          -v $(pwd)/{CACHE}:/cache \
          -v $(pwd)/results:/results \
          -v $(pwd)/data:/data \
          ghcr.io/sokrypton/colabfold:1.5.5-cuda12.2.2 \
          colabfold_batch {input.faa} {params.outdir}
        """

rule colabfold_host:
    input:
        faa = HOST_FAA
    output:
        done = touch(f"{COLF_OUT}/host/.done")
    params:
        outdir = f"{COLF_OUT}/host"
    shell:
        """
        docker run --rm --gpus all \
          -v $(pwd)/{CACHE}:/cache \
          -v $(pwd)/data:/data \
          ghcr.io/sokrypton/colabfold:1.5.5-cuda12.2.2 \
          colabfold_batch {input.faa} {params.outdir}
        """

rule foldseek_create_db:
    input:
        done = rules.colabfold_host.output.done,
        host_struct_dir = f"{COLF_OUT}/host"
    output:
        db = directory(f"{FSL_OUT}/host_db")
    conda: "envs/foldseek.yml"
    shell:
        "foldseek createdb {input.host_struct_dir} {output.db}"

rule foldseek_search:
    input:
        phage_done = rules.colabfold_phage.output.done,
        phage_struct_dir = f"{COLF_OUT}/phage_{s}",
        db   = rules.foldseek_create_db.output.db
    output:
        m8  = f"{FSL_OUT}/{s}/search_results.m8"
    params:
        tmpdir = f"{FSL_OUT}/{s}/tmp"
    conda: "envs/foldseek.yml"
    shell:
        "mkdir -p {FSL_OUT}/{s} && "
        "foldseek search {input.phage_struct_dir} {input.db} {output.m8} {params.tmpdir}"

rule parse_results:
    input:
        m8 = f"{FSL_OUT}/{s}/search_results.m8"
    output:
        tsv = f"{FSL_OUT}/{s}/interaction_predictions.tsv"
    run:
        cols = ['phage_protein','host_protein','identity','alnlen','mismatch',
                'gapopen','qstart','qend','tstart','tend','evalue','bits']
        df = pd.read_csv(input.m8, sep='\t', header=None, names=cols)
        # Clean up .pdb extension from protein names
        df['phage_protein'] = df['phage_protein'].str.replace('.pdb', '', regex=False)
        df['host_protein'] = df['host_protein'].str.replace('.pdb', '', regex=False)
        df = df[df.evalue < 1e-3].sort_values('evalue')
        df.to_csv(output.tsv, sep='\t', index=False)