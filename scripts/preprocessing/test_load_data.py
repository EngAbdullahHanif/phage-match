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
   
    with open(kmer_file, "r") as f:
        kmer_freqs = json.load(f)
    
    # initialize embedded_vector with the same shape as the first embedding vector in the embeddings dictionary
    embedded_vector = np.zeros_like(next(iter(embeddings.values())))
    total_weight = 0.0

    # !debug
    print(f"Initialized embedded_vector with shape: {embedded_vector.shape}")
    
    for kmer, freq in kmer_freqs.items():
        #! debug
        print(f"kmer: {kmer}, freq: {freq}")

        if kmer in embeddings:
            embedded_vector += freq * embeddings[kmer]
            #! debug
            print(f"embedded_vector: {embedded_vector}")
            print(f"embeddings[kmer]: {embeddings[kmer]}")
            total_weight += freq
    
    print(f"Total weight: {total_weight}")
    print(f"Final embedded_vector: {embedded_vector}")

    # Normalize the weighted sum
    if total_weight > 0:
        embedded_vector /= total_weight
    
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


