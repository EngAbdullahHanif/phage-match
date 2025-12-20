import numpy as np
import os

def one_hot_encode(sequence):
    """
    Converts a DNA sequence to a one-hot encoded matrix.
    """
    mapping = {'A': [1, 0, 0, 0], 'T': [0, 1, 0, 0], 'G': [0, 0, 1, 0], 'C': [0, 0, 0, 1]}
    return np.array([mapping.get(base, [0, 0, 0, 0]) for base in sequence])


def save_one_hot(seq_id, encoded_seq, output_dir):
    """
    Saves one-hot encoded matrix to a .npy file.
    """
    os.makedirs(output_dir, exist_ok=True)
    np.save(os.path.join(output_dir, f"{seq_id}.npy"), encoded_seq)
