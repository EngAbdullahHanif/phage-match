from collections import Counter
import json
import os

def kmer_frequencies(sequence, k):
    """
    Calculates k-mer frequencies for a DNA sequence.
    """
    kmers = [sequence[i:i+k] for i in range(len(sequence) - k + 1)]
    kmer_counts = Counter(kmers)
    total_kmers = sum(kmer_counts.values())
    return {kmer: count / total_kmers for kmer, count in kmer_counts.items()}

def save_kmer(seq_id, kmer_freqs, output_dir):
    """
    Saves k-mer frequencies to a JSON file.
    """
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, f"{seq_id}_kmer.json"), "w") as f:
        json.dump(kmer_freqs, f)
