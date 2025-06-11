import os
from Bio import SeqIO

# # def load_sequences(directory, file_ext=".fasta"):
# def load_sequences(directory, file_ext=".fna"):
#     """
#     Generator to load sequences from files in a directory.
#     """
#     # stop after loadig the first file
#     for root, _, files in os.walk(directory):
#         for file in files:
#             if file.endswith(file_ext):
#                 filepath = os.path.join(root, file)
#                 for record in SeqIO.parse(filepath, "fasta"):
#                     yield record.id, str(record.seq)


def load_sequences(directory, file_ext=".fna"):
    """
    Loads sequences from the first FASTA file found in each subdirectory.
    
    Args:
        directory (str): Path to the directory containing subdirectories with FASTA files.
        file_ext (str): File extension to look for (default is ".fna").
    
    Yields:
        tuple: A tuple containing sequence ID and sequence.
    """
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(file_ext):
                filepath = os.path.join(root, file)
                for record in SeqIO.parse(filepath, "fasta"):
                    yield record.id, str(record.seq)
                break  # Stop after processing the first file in the directory

