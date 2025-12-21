Manifests define the inputs for a run. Use the small demo manifests for GitHub demos and keep real data local.

Files
- hosts.tsv: demo host inputs
- phages.tsv: demo phage inputs
- hosts_real.tsv: larger real-data template
- phages_real.tsv: larger real-data template

Format
Each file is a tab-separated table with a header row.

hosts.tsv
- host_id: stable ID for the host isolate
- genome_fna: path to host genome FASTA (.fna)
- proteome_faa: path to host proteome FASTA (.faa)

phages.tsv
- phage_id: stable ID for the phage
- fasta: path to phage genome FASTA (.fna)

Examples
hosts.tsv
host_id	genome_fna	proteome_faa
H001	data/inputs/hosts/H001.fna	data/inputs/hosts/H001.faa

phages.tsv
phage_id	fasta
P001	data/library/phages/P001.fna
P002	data/library/phages/P002.fna
P003	data/library/phages/P003.fna

Notes
- Keep real datasets out of git; point these files to local paths instead.
- Paths can be absolute or relative to the repo root.
