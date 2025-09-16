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


# --- Global variables for lazy loading ---
model = None
tokenizer = None


def load_resources():
    """Load the model and tokenizer into global variables if they haven't been already."""
    global model, tokenizer
    if model is None:
        logging.info("Lazy loading Keras model...")
        model = load_model(MODEL_PATH)
        logging.info("Model loaded.")
    if tokenizer is None:
        logging.info("Lazy loading tokenizer...")
        with open(TOKENIZER_PATH, "rb") as handle:
            tokenizer = pickle.load(handle)
        logging.info("Tokenizer loaded.")


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
    # Lazy load resources on the first request
    load_resources()

    try:
        data = request.get_json(force=True)
        text = data.get("text", "")

        if not text:
            logging.warning("Prediction request received with no 'text' field.")
            return jsonify({"error": 'The "text" field is missing.'}), 400

        # Preprocess the text
        sequences = tokenizer.texts_to_sequences([text])
        processed_text = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH)

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
