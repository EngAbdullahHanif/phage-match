from multiprocessing import Pool
from .one_hot_encode import one_hot_encode, save_one_hot
from .kmer_calculation import kmer_frequencies, save_kmer

def process_one_hot(args):
    seq_id, sequence, output_dir = args
    encoded_seq = one_hot_encode(sequence)
    save_one_hot(seq_id, encoded_seq, output_dir)

def process_kmers(args):
    seq_id, sequence, output_dir, k = args
    kmer_freqs = kmer_frequencies(sequence, k)
    save_kmer(seq_id, kmer_freqs, output_dir)

def parallel_process(func, data, num_workers):
    """
    Generic function for parallel processing.
    """
    with Pool(num_workers) as pool:
        pool.map(func, data)


