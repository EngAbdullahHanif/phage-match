**Workflow Overview: Steps Completed So Far**

1. **Data Preprocessing**

   - **Input Data:** Raw genomic data from the directories `data/raw/bacterial_genomes`, `data/raw/phage_genomes`, and `data/raw/gene_annotations`.
   - **Processing:**
     - Loaded sequences using `load_sequences` function (leveraging Biopython).
   - **Output:** Preprocessed data files saved in `data/processed/`.

2. **One-Hot Encoding**

   - **Function:** Applied `one_hot_encode` to convert DNA sequences into binary matrices for machine learning.
   - **Output Files:** Saved one-hot encoded files as `.npy` in `data/processed/one_hot_encoded/`.

3. **K-mer Frequencies**

   - **Function:** Used `kmer_frequencies` to calculate k-mer distributions for the DNA sequences.
   - **Output Files:** Saved k-mer frequency files as `.json` in `data/processed/kmer_frequencies/`.

4. **DNA2Vec Embeddings**

   - **Function:** Loaded pre-trained DNA2Vec embeddings and mapped k-mers to dense vector representations.
   - **Output Files:** Saved embeddings as `.npy` files in `data/processed/embeddings/`.

5. **Dimensionality Reduction**

   - **Techniques Used:**
     - PCA for linear patterns, t-SNE for visualization, and autoencoders for non-linear compressions.
   - **Output Files:** Reduced feature datasets saved under `data/processed/reduced/`:
     ```
     data/processed/reduced/
         pca/
         tsne/
         autoencoders/
     ```

6. **Feature Selection**
   - **Focus:** Identifying and extracting CRISPR sequences and prophage regions.
   - **Tools Used:**
     - PHASTER for prophage identification.
     - CRISPRCasFinder for CRISPR-associated regions.
   - **Output Files:**
     - `data/processed/features/crispr_features.csv`
     - `data/processed/features/prophage_features.csv`

---

### **Workflow Summary**

- **Flow:** Data → Preprocessing → One-Hot Encoding / K-mer Frequencies / DNA2Vec Embeddings → Dimensionality Reduction → Feature Selection.
- **Files:** Processed outputs are modular and saved in their respective subdirectories in `data/processed/`.
- **Next Steps:** Continue integrating the selected features into the machine learning pipeline for predicting phage-bacteria interactions.
