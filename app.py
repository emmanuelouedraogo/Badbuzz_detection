# /full/path/to/your/project/badbuzz_detection/app.py
# Set TensorFlow log level before any other imports.
# 0 = all messages, 1 = filter INFO, 2 = filter WARNING, 3 = filter ERROR
import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import logging
import numpy as np
from flask import Flask, request, jsonify
import pickle
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.saving import load_model

# --- Configuration & Logging ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Constants ---
# Path to the model and tokenizer
MODEL_PATH = os.path.join("saved_model", "best_gensim_bidirectional_gru_en_model.keras")
TOKENIZER_PATH = "tokenizer.pickle"
MAX_SEQUENCE_LENGTH = 200  # IMPORTANT: Must be the same value used during training


# --- Flask App Initialization ---
app = Flask(__name__)  # Create the Flask app instance


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

    sequences = tokenizer.texts_to_sequences([text])
    padded_sequence = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH)

    return padded_sequence


# --- Model & Tokenizer Loading ---

# These objects are loaded once at startup for better performance.
logging.info("Loading Keras model...")
try:
    model = load_model(MODEL_PATH)
    logging.info("Model loaded successfully.")
except Exception as e:
    logging.error(f"Error loading model from {MODEL_PATH}: {e}")
    raise RuntimeError(f"Could not load Keras model from {MODEL_PATH}.") from e

logging.info("Loading tokenizer...")
try:
    with open(TOKENIZER_PATH, "rb") as handle:
        tokenizer = pickle.load(handle)
    logging.info("Tokenizer loaded successfully.")
except FileNotFoundError:
    logging.error(f"Error: Tokenizer file not found at '{TOKENIZER_PATH}'.")
    raise RuntimeError(f"Tokenizer file not found at {TOKENIZER_PATH}.")
except Exception as e:
    logging.error(f"Error loading tokenizer: {e}")
    raise RuntimeError("Could not load tokenizer pickle file.") from e


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to confirm the service is running and the model is loaded."""
    # A simple check to see if the model and tokenizer objects exist
    if model is not None and tokenizer is not None:
        return jsonify({"status": "healthy"}), 200
    else:
        logging.error("Health check failed: model or tokenizer not loaded.")
        return (
            jsonify({"status": "unhealthy", "reason": "Model or tokenizer not loaded"}),
            503,
        )


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
        prediction_score = model.predict(processed_text, verbose=0)[0][0]

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

    except Exception:
        logging.exception("An error occurred during prediction.")
        return jsonify({"error": "An internal server error occurred."}), 500


if __name__ == "__main__":
    # For development, debug=True is fine. For production, use a WSGI server.
    # Example with Waitress: waitress-serve --host 0.0.0.0 --port 5000 app:app
    app.run(host="0.0.0.0", port=5000, debug=False)
