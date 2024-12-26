import yaml
import logging

from scripts.preprocessing.load_data import load_sequences
from scripts.preprocessing.parallel_utils import parallel_process, process_one_hot, process_kmers
from scripts.embeddings import process_embeddings


# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("pipeline.log"),
                        logging.StreamHandler()
                    ])

def run_pipeline(config_path):
    """
    Runs the genomic data preprocessing pipeline.
    
    Args:
        config_path (str): Path to the configuration YAML file.
    """

    logging.info("starting pipeline and loading configuration")
    

    # Load the configuration file
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)


    # List of all data types and their input/output directories
    data_types = [
        # {
        #     "name": "bacterial_genomes",
        #     "input_dir": config["input_dirs"]["bacterial_genomes"],
        #     "one_hot_output": f"{config['output_dirs']['one_hot_encoded']}/bacterial_genomes",
        #     "kmer_output": f"{config['output_dirs']['kmer_frequencies']}/bacterial_genomes"
        # },
        {
            "name": "gene_annotations_bacterial",
            "input_dir": config["input_dirs"]["gene_annotations_bacterial"],
            "one_hot_output": f"{config['output_dirs']['one_hot_encoded']}/gene_annotations_bacterial",
            "kmer_output": f"{config['output_dirs']['kmer_frequencies']}/gene_annotations_bacterial"
        },
        {
            "name": "gene_annotations_phage",
            "input_dir": config["input_dirs"]["gene_annotations_phage"],
            "one_hot_output": f"{config['output_dirs']['one_hot_encoded']}/gene_annotations_phage",
            "kmer_output": f"{config['output_dirs']['kmer_frequencies']}/gene_annotations_phage"
        },
        {
            "name": "phage_genomes",
            "input_dir": config["input_dirs"]["phage_genomes"],
            "one_hot_output": f"{config['output_dirs']['one_hot_encoded']}/phage_genomes",
            "kmer_output": f"{config['output_dirs']['kmer_frequencies']}/phage_genomes"
        }
    ]

    # for data_type in data_types:

    #     logging.info("loading data")

    #     # Prepare data for one-hot encoding
    #     one_hot_data = [
    #         (seq_id, seq, data_type["one_hot_output"])
    #         for seq_id, seq in load_sequences(data_type["input_dir"])
    #     ]

    #     # Prepare data for k-mer calculation
    #     kmer_data = [
    #         (seq_id, seq, data_type["kmer_output"], config["kmer_k"])
    #         for seq_id, seq in load_sequences(data_type["input_dir"])
    #     ]

    #     logging.info("processing data")

    #     # Process one-hot encoding in parallel
    #     parallel_process(process_one_hot, one_hot_data, config["num_workers"])

    #     # Process k-mer frequencies in parallel
    #     parallel_process(process_kmers, kmer_data, config["num_workers"])

    
    # After processing k-mers, generate DNA2Vec embeddings
    logging.info("Generating DNA2Vec embeddings")
    process_embeddings(
        kmer_dir=config["input_dirs"]["kmer_frequencies"],
        embedding_file=config["embedding_file"],
        output_dir=config["output_dirs"]["embeddings"]
    )
    logging.info("DNA2Vec embeddings generation complete")



    logging.info("pipeline complete")


if __name__ == "__main__":
    # Run the pipeline
    run_pipeline("config.yaml")
