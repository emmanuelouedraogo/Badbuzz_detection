# /full/path/to/your/project/badbuzz_detection/app.py
import os
import sys
import logging
import numpy as np
from flask import Flask, request, jsonify
from keras.preprocessing.sequence import pad_sequences
import pickle
import requests
from dotenv import load_dotenv
from keras.saving import load_model

# --- Configuration & Logging ---
load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Constants ---
# Path to the model and tokenizer
MODEL_PATH = os.path.join("saved_model", "best_gensim_bidirectional_gru_en_model.keras")
TOKENIZER_PATH = "tokenizer.pickle"
MAX_SEQUENCE_LENGTH = 200  # IMPORTANT: Must be the same value used during training


# --- Helper function to download model/tokenizer if they don't exist ---
def download_file_if_not_exists(filepath, url_env_var):
    """Downloads a file from a URL if it doesn't exist locally."""
    if not os.path.exists(filepath):
        url = os.getenv(url_env_var)
        if url:
            logging.info(f"File '{filepath}' not found. Downloading from {url}...")
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with requests.get(url, stream=True) as r:
                    r.raise_for_status()
                    with open(filepath, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                logging.info(f"Successfully downloaded '{filepath}'.")
            except Exception as e:
                logging.error(f"Failed to download file from {url}. Error: {e}")
                sys.exit(1)
        else:
            logging.error(
                f"File '{filepath}' not found and no download URL ('{url_env_var}') provided in .env file."
            )
            sys.exit(1)

# --- Flask App Initialization ---
app = Flask(__name__)


# --- Model & Tokenizer Loading ---
download_file_if_not_exists(MODEL_PATH, "MODEL_URL")
download_file_if_not_exists(TOKENIZER_PATH, "TOKENIZER_URL")

# These objects are loaded once at startup for better performance.
logging.info("Loading Keras model...")
try:
    model = load_model(MODEL_PATH)
    logging.info("Model loaded successfully.")
except Exception as e:
    logging.error(f"Error loading model from {MODEL_PATH}: {e}")
    sys.exit(1)  # Exit if the core component fails to load

logging.info("Loading tokenizer...")
try:
    with open(TOKENIZER_PATH, "rb") as handle:
        tokenizer = pickle.load(handle)
    logging.info("Tokenizer loaded successfully.")
except FileNotFoundError:
    logging.error(f"Error: Tokenizer file not found at '{TOKENIZER_PATH}'.")
    sys.exit(1)
except Exception as e:
    logging.error(f"Error loading tokenizer: {e}")
    sys.exit(1)


def preprocess_text(text: str) -> np.ndarray:
    """
    Preprocesses raw text to be compatible with the model.
    1. Tokenizes the text
    2. Converts to a sequence of integers
    3. Applies padding
    """
    if not tokenizer:
        # This check is now redundant due to sys.exit() on load failure, but good for safety
        raise RuntimeError("Tokenizer is not available.")

    # Convertit le texte en une séquence d'entiers
    sequences = tokenizer.texts_to_sequences([text])

    # Applique le padding pour avoir une longueur de séquence fixe
    padded_sequence = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH)

    return padded_sequence


@app.route("/predict", methods=["POST"])
def predict():
    """Endpoint for sentiment prediction."""
    try:
        data = request.get_json(force=True)
        text = data.get("text", "")

        if not text:
            logging.warning("Prediction request received with no 'text' field.")
            return jsonify({"error": 'The "text" field is missing.'}), 400

        # Preprocess the text
        processed_text = preprocess_text(text)

        # Prediction
        prediction_score = model.predict(processed_text)[0][0]

        # Interpretation of the score (threshold at 0.5).
        # Based on user feedback, the model's output convention is:
        # A score close to 1 is NEGATIVE, and a score close to 0 is POSITIVE.
        # Example: "Bad job" was getting a high score and being labeled "Positive".
        label = "Negative" if prediction_score > 0.5 else "Positive"

        # Create the response
        response = {"prediction": label, "confidence_score": float(prediction_score)}
        logging.info(
            f"Prediction for text '{text[:30]}...': {label} ({prediction_score:.4f})"
        )
        return jsonify(response)

    except Exception as e:
        logging.exception("An error occurred during prediction.")
        return jsonify({"error": "An internal server error occurred."}), 500


if __name__ == "__main__":
    # For development, debug=True is fine. For production, use a WSGI server.
    # Example with Waitress: waitress-serve --host 0.0.0.0 --port 5000 app:app
    app.run(host="0.0.0.0", port=5000, debug=False)
