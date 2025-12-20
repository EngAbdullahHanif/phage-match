import numpy as np
import os

from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense
from tensorflow.keras.optimizers import Adam




def apply_pca(input_dir, output_dir, n_components=2):
    """
    Apply PCA to reduce dimensions of data.
    """
    os.makedirs(output_dir, exist_ok=True)

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".npy"):  # Assuming data is stored in NumPy arrays
                data = np.load(os.path.join(root, file))

                # Debugging: data is 1D, and t-SNE requires at least 2D data, it is 1D, becuase I have not completed the previous steps, DNA2Vec embeddings, Kmer frequencies, one-hot encoding, all of are only checked in the pipeline_main.py, not applied completely

                if data.size == 0:
                    print(f"Skipping {file}: Data is empty.")
                    continue

                if data.ndim == 1:
                    print(f"Skipping {file}: Data is 1D.")
                    data = data.reshape(1, -1)  # Ensure data is 2D

                if data.shape[0] < n_components:
                    print(f"Skipping {file}: Not enough samples for {n_components} components.")
                    continue



                pca = PCA(n_components=n_components)
                reduced_data = pca.fit_transform(data)
                
                # Save the reduced data
                output_file = os.path.join(output_dir, file)
                np.save(output_file, reduced_data)
                print(f"PCA applied and saved: {output_file}")


def apply_tsne(input_dir, output_dir, n_components=2, perplexity=30, learning_rate=200, n_iter=1000):
    """
    Apply t-SNE to reduce dimensions of data.
    """
    os.makedirs(output_dir, exist_ok=True)

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".npy"):  # Assuming data is stored in NumPy arrays
                data = np.load(os.path.join(root, file))

                # data is 1D, and t-SNE requires at least 2D data, it is 1D, becuase I have not completed the previous steps, DNA2Vec embeddings, Kmer frequencies, one-hot encoding, all of are only checked in the pipeline_main.py, not applied completely
                if data.ndim == 1:
                    print(f"Skipping {file}: Data is 1D.")
                    continue

                if data.shape[0] <= 1:
                    print(f"Skipping {file}: Not enough samples for {n_components} components.")
                    continue

                if data.shape[0] <= perplexity:
                    perplexity = max(1, data.shape[0] - 1)  # Adjust perplexity dynamically
                    print(f"Adjusting perplexity to {perplexity} for file: {file}")



                tsne = TSNE(n_components=n_components, perplexity=perplexity, learning_rate=learning_rate, n_iter=n_iter)
                reduced_data = tsne.fit_transform(data)

                # Save the reduced data
                output_file = os.path.join(output_dir, file)
                np.save(output_file, reduced_data)
                print(f"t-SNE applied and saved: {output_file}")


def build_autoencoder(input_dim, hidden_units):
    """
    Build and compile an autoencoder model.
    """
    input_layer = Input(shape=(input_dim,))
    encoded = Dense(hidden_units, activation="relu")(input_layer)
    decoded = Dense(input_dim, activation="sigmoid")(encoded)
    autoencoder = Model(inputs=input_layer, outputs=decoded)
    autoencoder.compile(optimizer=Adam(), loss="mse")
    return autoencoder


def apply_autoencoder(input_dir, output_dir, hidden_units=64, epochs=50, batch_size=32):
    """
    Train an autoencoder and apply it to reduce data dimensions.
    """
    os.makedirs(output_dir, exist_ok=True)

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".npy"):
                data = np.load(os.path.join(root, file))
                
                # Debugging data is 1D, and t-SNE requires at least 2D data, it is 1D, becuase I have not completed the previous steps, DNA2Vec embeddings, Kmer frequencies, one-hot encoding, all of are only checked in the pipeline_main.py, not applied completely
                if data.size == 0:
                    print(f"Skipping {file}: Empty array.")
                    continue

                if data.ndim != 2 or data.shape[1] <= 0:
                    print(f"Skipping {file}: Invalid data shape {data.shape}. Expected 2D array with features.")
                    continue
                
                # Build and train the autoencoder
                autoencoder = build_autoencoder(data.shape[1], hidden_units)
                autoencoder.fit(data, data, epochs=epochs, batch_size=batch_size, verbose=1)
                
                # Extract reduced dimensions (encoded representation)
                encoder = Model(inputs=autoencoder.input, outputs=autoencoder.layers[1].output)
                reduced_data = encoder.predict(data)

                # Save the reduced data
                output_file = os.path.join(output_dir, file)
                np.save(output_file, reduced_data)
                print(f"Autoencoder applied and saved: {output_file}")
