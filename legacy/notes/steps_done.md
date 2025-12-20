# Phase 1: Bacterial Host Genome Curation

Below is a step-by-step summary of everything we ran, the custom scripts we created, and where the outputs live.

1. Quality Control of Raw Reads  
   • Tool: FastQC  
   • Command (from your raw reads dir):

   ```bash
   fastqc *.fastq -o data/processed/qc_reports
   ```

   • Output: one HTML report per FASTQ in  
    qc_reports

2. Genome Completeness & Contamination  
   • Tool: CheckM  
   • Setup & download reference data (only once):

   ```bash
   checkm data setRoot data/checkm_data
   checkm data download
   ```

   • Run lineage workflow on your assembled FASTA bins:

   ```bash
   checkm lineage_wf -x fna -t 8 \
     data/E_coli_genomes/Genomes_ID \
     data/processed/checkm_out
   ```

   • Key outputs (in storage):

   - `bin_stats.tree.tsv` — completeness & contamination per bin
   - `bin_stats_ext.tsv` — extended genome stats (GC, N50, etc.)
   - `marker_gene_stats.tsv`, `phylo_hmm_info.pkl.gz`, etc.

3. Antibiotic Resistance Annotation  
   • Tool: Abricate (ResFinder DB)  
   • Command (from your genome dir):

   ```bash
   abricate --db resfinder \
     data/E_coli_genomes/Genomes_ID/*.fna \
     > data/E_coli_genomes/Genomes_ID/resistance_genes.tsv
   ```

   • Output:  
    `resistance_genes.tsv` in the genomes folder

4. Virulence Factor Annotation  
   • Custom wrapper: vfdb.py  
   • Created vfdb.py, which loops over each FASTA and runs  
    `abricate --db vfdb`.  
   • Run it like:

   ```bash
   python scripts/vfdb.py \
     -i data/E_coli_genomes/Genomes_ID \
     -o data/processed/virulence_factors
   ```

   • Outputs: one TSV per genome in  
    virulence_factors (e.g. `EC958_vfdb.tsv`)

5. Genomic Feature Extraction  
   a) GC Content  
   • Script: compute_gc_content.py  
    – Reads each genome FASTA, calculates GC% per contig, averages it  
    – Writes a CSV  
   • Run:

   ```bash
   python scripts/compute_gc_content.py \
     -i data/E_coli_genomes/Genomes_ID \
     -o data/processed/genomic_features/gc_content.csv
   ```

   • Output:  
    gc_content.csv

   b) 3-mer Frequencies  
   • Tool: Jellyfish  
   • Commands:

   ```bash
   # build k-mer db
   jellyfish count -m 3 -s 100M -C \
     data/E_coli_genomes/Genomes_ID/*.fna \
     -o data/processed/genomic_features/mer_counts.jf

   # dump k-mer + counts
   jellyfish dump -c \
     data/processed/genomic_features/mer_counts.jf \
     > data/processed/genomic_features/mer_counts.fa
   ```

   • Outputs:

   - `mer_counts.jf` (binary DB)
   - `mer_counts.fa` (text k-mer → count table)

6. Prophage Detection  
   • Approach: PHASTER URLAPI  
   • Script: phaster_api.py  
    – Submits each bacterial genome FASTA to PHASTER’s API  
    – Polls until “Complete”  
    – Downloads `<sample>.zip` into prophage  
   • Run:
   ```bash
   pip install requests tqdm
   python scripts/phaster_api.py \
     -i data/E_coli_genomes/Genomes_ID \
     -o data/processed/prophage
   ```
   • Outputs: for each `<sample>.zip` under prophage.  
    Inside each ZIP you’ll find the tab-delimited prophage region table  
    (can be renamed to BED) and annotated GenBank.

Deliverables for Phase 1

---

• **Cleaned genomes** with passing QC & CheckM metrics  
• `resistance_genes.tsv` & `*_vfdb.tsv` (resistance + virulence)  
• `gc_content.csv` & `mer_counts.fa` (GC % + 3-mer frequencies)  
• `*.zip` + extracted region tables (prophage coordinates)

# Phase 2: Phage Phenotypic Data Integration

Below is a detailed record of every task you completed, the inputs you used, the scripts you wrote, and the outputs generated. You can copy this into your notes or share with your teammate.

---

## 1) Inhibition Efficiency Scores

**Goal:** Normalize spot‐test category (0–3) data to a 0–1 interaction matrix.  
**Input:**

- Excel file SST_E_coli_and_Salmonella_phages.xlsx
- Sheet name: `"category"`  
  **Script:**
- compute_inhibition_scores.py
  - Loads the “category” sheet
  - Extracts the host IDs (first column) and phage columns
  - Divides all values by 3.0 → normalized 0–1 matrix
  - Saves CSV with `host_id` as row index and phage names as columns  
    **Command:**

```bash
pip install pandas openpyxl
python scripts/compute_inhibition_scores.py \
  -i data/metadata/SST_E_coli_and_Salmonella_phages.xlsx \
  -s category \
  -o data/processed/phenotypes/inhibition_efficiency.csv
```

**Output:**

- inhibition_efficiency.csv
  - A table of normalized interaction strengths (0–1)

---

## 2) Virulence Index Placeholder

**Goal:** Create a placeholder “virulence index” from binary infection data (0/1) and merge with inhibition efficiencies.  
**Inputs:**

- Binary infection matrix
  - sst_e_coli_phages.xlsx (sheet `"binary"`)
- Normalized inhibition CSV from step 1
  - inhibition_efficiency.csv  
    **Script:**
- compute_virulence_index.py
  - Reads the binary sheet (or CSV) into a DataFrame
  - Maps `1 → 1.0`, `0 → 0.2` to form `virulence_index`
  - Reads the inhibition CSV into a DataFrame
  - Melts both matrices into long‐form (`host_id`, `phage`, value)
  - Merges on `host_id` + `phage`
  - Writes combined phenotypic metadata CSV  
    **Command:**

```bash
pip install pandas openpyxl
python scripts/compute_virulence_index.py \
  -b data/metadata/sst_e_coli_phages.xlsx \
  -s binary \
  -i data/processed/phenotypes/inhibition_efficiency.csv \
  -o data/processed/phenotypes/phenotypic_metadata.csv
```

**Output:**

- phenotypic_metadata.csv
  - Columns: `host_id, phage, inhibition_efficiency, virulence_index`

---

## 3) Interaction Heatmap Visualization

**Goal:** Cluster and visualize the normalized interaction matrix as a heatmap.  
**Input:**

- Normalized inhibition CSV
  - inhibition_efficiency.csv  
    **Script:**
- plot_interaction_heatmap.py
  - Loads CSV into pandas
  - Uses Seaborn `clustermap` (Viridis palette)
  - Saves high‐resolution PNG  
    **Command:**

```bash
pip install pandas seaborn matplotlib
python scripts/plot_interaction_heatmap.py \
  -i data/processed/phenotypes/inhibition_efficiency.csv \
  -o data/processed/phenotypes/interaction_heatmap.png
```

**Output:**

- interaction_heatmap.png
  - Clustered heatmap of hosts vs. phages (color = interaction strength)

---

## 4) Phage Lifestyle Prediction

**Goal:** Predict each phage’s lifestyle (lytic vs. temperate) using PHACTS; label un‐sequenced phages as “unknown.”  
**Input:**

- Phage genome FASTAs in `raw/phage_genomes/` (e.g. `phA11.fasta`, etc.)  
  **Script:**
- predict_phage_lifestyle.py
  - Iterates over each FASTA in the input directory
  - Runs `phacts predict -i <fasta> -o <phage>_phacts.json`
  - Parses JSON for `"lifestyle"` field
  - Aggregates all results into a summary CSV  
    **Command:**

```bash
pip install phacts requests pandas
python scripts/predict_phage_lifestyle.py \
  -i raw/phage_genomes \
  -o data/processed/phenotypes/lifestyle
```

**Outputs:**

- For each phage:
  - `data/processed/phenotypes/lifestyle/<phage_id>_phacts.json`
- Summary table:
  - lifestyle_summary.csv
    - Columns: `phage, lifestyle`

---

### Summary of Phase 2 Deliverables

- **inhibition_efficiency.csv** — normalized 0–1 interaction matrix
- **phenotypic_metadata.csv** — combined inhibition + virulence index
- **interaction_heatmap.png** — clustered heatmap visualization
- **lifestyle_summary.csv** — phage lifestyle calls (lytic/temperate/unknown) plus individual JSON outputs

These files live under phenotypes and capture your complete Phase 2 work.

### Phase 3: Phage Genome Analysis

Below is a detailed record of every task you completed in Phase 3, the inputs you used, the scripts/tools you ran, the commands, and the outputs generated.

---

## 1) Genome Annotation with Prokka

**Goal:** Generate NCBI-compliant GenBank annotations and protein FASTAs for each phage.  
**Input:**  
 • Raw phage genome FASTA files in `raw/phage_genomes/` (e.g. `phA11.fasta`, `phB7.fasta`, …)  
**Tool:**  
 • Prokka  
**Command (example for phA11):**

```bash
prokka \
  --outdir data/processed/annotations/phage_genomes/phA11_annotation \
  --prefix phA11 \
  raw/phage_genomes/phA11.fasta
```

**Outputs (per phage under `…/phX_annotation/`):**  
 • phX.gbk (GenBank file)  
 • phX.faa (predicted proteins)  
 • phX.gff, phX.fna, phX.tbl, etc.

---

## 2) RBP Prediction via HHsearch (HHPred)

**Goal:** Identify structural homologs of each predicted protein (candidate RBPs).  
**Input:**  
 • Prokka protein FASTAs: `…/phX_annotation/phX.faa`  
 • HHsearch database: `db/pdb70`  
**Script:**  
 • predict_rbps.py  
**Command:**

```bash
python scripts/predict_rbps.py \
  -i data/processed/annotations/phage_genomes \
  -o data/processed/annotations/rbp_predictions \
  -d db/pdb70 \
  -p interproscan-5.65-97.0/interproscan.sh
```

**Outputs:**  
 • `data/processed/annotations/rbp_predictions/hhsearch/<seq_id>_hhsearch.txt`  
 (one HHPred/HHSuite tabbed output per protein)

---

## 3) Structural Domain Annotation with InterProScan

**Goal:** Annotate Pfam / TIGRFAM domains on each protein.  
**Input:**  
 • Same Prokka `.faa` files as above  
 • Completed HHsearch outputs (optional—script will warn if missing)  
**Script:**  
 • resume_interproscan.py  
**Command (limiting to Pfam + TIGRFAM):**

```bash
python scripts/resume_interproscan.py \
  -i data/processed/annotations/phage_genomes \
  -o data/processed/annotations/rbp_predictions \
  -p interproscan-5.65-97.0/interproscan.sh \
  --appl Pfam,TIGRFAM
```

**Outputs:**  
 • `data/processed/annotations/rbp_predictions/interpro/<phage_id>_interpro.tsv`  
 (one TSV per phage, columns: seq_id, md5, length, db, acc, desc, start, end, evalue, …)

---

## 4) tRNA Detection with Aragorn

**Goal:** Find tRNA genes (lysogeny markers) in each phage genome.  
**Input:**  
 • Prokka‐annotated genome FASTA (`.fna`) for each phage under `…/phX_annotation/`  
**Script:**  
 • detect_trnas.py  
**Command:**

```bash
python scripts/detect_trnas.py \
  -i data/processed/annotations/phage_genomes \
  -o data/processed/annotations/tRNA_reports
```

**Outputs:**  
 • `data/processed/annotations/tRNA_reports/<phage_id>_tRNA.out`  
 (Aragorn report per genome, including anticodon, coordinates, secondary structure)

---

### Summary of Phase 3 Deliverables

- **Annotated genomes**: `data/processed/annotations/phage_genomes/*_annotation/*.gbk`
- **RBP HHsearch results**:  
  `data/processed/annotations/rbp_predictions/hhsearch/*.txt`
- **RBP domain annotations**:  
  `data/processed/annotations/rbp_predictions/interpro/*.tsv`
- **tRNA reports**:  
  `data/processed/annotations/tRNA_reports/*.out`
