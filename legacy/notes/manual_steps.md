#### Adding the `HADDOCK` Docking Step

This is not something you should automate in this pipeline. Docking is a complex, follow-up analysis. The correct workflow is:

1.  **Run the entire Snakemake pipeline first.** This will give you your `interaction_predictions.tsv` file(s).
2.  **Analyze the results.** Look at the `interaction_predictions.tsv` file and find the top 1-3 most promising phage-host protein pairs (the ones with the best `evalue` from Foldseek).
3.  **Perform manual docking.** Take the specific `.pdb` files for those few top pairs (e.g., `phage_protein_X.pdb` and `host_protein_Y.pdb`) and submit them to the HADDOCK web server or a local installation. This is a separate, focused step to validate your best hits from the pipeline.
