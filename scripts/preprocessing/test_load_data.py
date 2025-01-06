import os
import json
import numpy as np
from multiprocessing import Pool

def load_dna2vec(filepath):
    """
    Load pre-trained DNA2Vec embeddings from a file.
    """
    embeddings = {}
    with open(filepath, "r") as f:
        for line in f:
            values = line.strip().split()
            kmer = values[0]
            vector = np.array([float(v) for v in values[1:]])
            embeddings[kmer] = vector
    return embeddings


def embed_kmers(kmer_file, embeddings):
    """
    Map k-mers from a k-mer frequency file to DNA2Vec embeddings.
    """
    # Load k-mer frequencies from the input file
    with open(kmer_file, "r") as f:
        kmer_freqs = json.load(f)

    # Validate embeddings and extract dimension
    first_kmer = next(iter(embeddings.keys()), None)
    if not first_kmer or not isinstance(embeddings[first_kmer], (list, np.ndarray)):
        raise ValueError("Embeddings are missing or incorrectly formatted.")
    
    embedding_dim = len(embeddings[first_kmer])
    if embedding_dim <= 0:
        raise ValueError("Embedding dimension must be positive and non-zero.")
    
    print(f"Embedding dimension detected: {embedding_dim}")

    # Initialize embedded_vector with the correct shape
    embedded_vector = np.zeros(embedding_dim, dtype=np.float64)
    print(f"Initialized embedded_vector with shape: {embedded_vector.shape}")

    total_weight = 0.0

    for kmer, freq in kmer_freqs.items():
        freq = float(freq)  # Ensure freq is a scalar

        # Check if the k-mer exists in the embeddings dictionary
        if kmer in embeddings:
            embedding = np.array(embeddings[kmer], dtype=np.float64)  # Convert to numpy array

            # Validate shape consistency
            if embedding.shape == embedded_vector.shape:
                embedded_vector += freq * embedding
                total_weight += freq
            else:
                print(f"Skipping k-mer {kmer} due to mismatched shape: {embedding.shape} (expected {embedded_vector.shape})")
        else:
            print(f"Warning: Missing embedding for k-mer {kmer}")

    # Normalize the embedded vector
    if total_weight > 0:
        embedded_vector /= total_weight
        print(f"Normalized embedded_vector with shape: {embedded_vector.shape}")
    else:
        print("Warning: Total weight is zero. Returning unmodified embedded_vector.")

    # Log invalid embeddings
    with open("skipped_kmers.log", "w") as log_file:
        for kmer, embedding in embeddings.items():
            if not isinstance(embedding, (list, np.ndarray)) or len(embedding) != 100:
                log_file.write(f"{kmer}: {embedding}\n")

    return embedded_vector


def save_embedding(seq_id, vector, output_dir):
    """
    Save the embedding vector as a .npy file.
    """
    os.makedirs(output_dir, exist_ok=True)
    np.save(os.path.join(output_dir, f"{seq_id}.npy"), vector)


def parallel_process_embeddings(args):
    """
    Helper function for parallel processing of embeddings.
    """
    kmer_file, embeddings, output_dir = args
    seq_id = os.path.splitext(os.path.basename(kmer_file))[0]
    embedded_vector = embed_kmers(kmer_file, embeddings)
    save_embedding(seq_id, embedded_vector, output_dir)
    print(f"Saved embedding for {seq_id}")


def process_embeddings(kmer_dir, embedding_file, output_dir):
    """
    Process all k-mer files in a directory and save embeddings using multiprocessing.
    """
    embeddings = load_dna2vec(embedding_file)

    # Debugging: 
    # for kmer, vector in embeddings.items():
    #     print(f"k-mer: {kmer}, shape: {vector.shape}")

    # Prepare arguments for parallel processing
    args_list = []
    for root, _, files in os.walk(kmer_dir):
        for file in files:
            if file.endswith(".json"):
                kmer_file = os.path.join(root, file)
                seq_id = os.path.splitext(file)[0]  # Extract sequence ID from filename
                args_list.append((kmer_file, embeddings, output_dir))

    # Use multiprocessing to process embeddings
    with Pool(processes=4) as pool:  # Adjust `processes` based on your system
        pool.map(parallel_process_embeddings, args_list)
    
    print("All embeddings saved successfully.")


