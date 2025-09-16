# /full/path/to/your/project/badbuzz_detection/app.py
# Set TensorFlow log level before any other imports.
# 0 = all messages, 1 = filter INFO, 2 = filter WARNING, 3 = filter ERROR
import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import logging
from flask import Flask, request, jsonify
import pickle

# --- Configuration & Logging ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Constants ---
# Path to the model and tokenizer
MODEL_PATH = os.path.join("saved_model", "best_model.pkl")
VECTORIZER_PATH = "best_vectorizer.pkl"


# --- Flask App Initialization ---
app = Flask(__name__)  # Create the Flask app instance


# --- Global variables for lazy loading ---
model = None
vectorizer = None


def load_resources():
    """Load the model and tokenizer into global variables if they haven't been already."""
    global model, vectorizer
    if model is None:
        logging.info("Lazy loading Scikit-learn model...")
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        logging.info("Model loaded.")
    if vectorizer is None:
        logging.info("Lazy loading TfidfVectorizer...")
        with open(VECTORIZER_PATH, "rb") as f:
            vectorizer = pickle.load(f)
        logging.info("Vectorizer loaded.")


@app.route("/", methods=["GET"])
def index():
    """Root endpoint to provide a simple status message."""
    return jsonify({"message": "Bad Buzz Detection API is running."}), 200


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to confirm the service is running."""
    # This endpoint should be lightweight and only confirm that the server process is alive.
    # The actual model loading is handled lazily by the /predict endpoint.
    # A failed health check here would mean the web server (e.g., Waitress) is down.
    return jsonify({"status": "ok"}), 200


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
        processed_text = vectorizer.transform([text])

        # Prediction
        # predict_proba returns [[P(neg), P(pos)]]. We use the score for the positive class.
        prediction_proba = model.predict_proba(processed_text)[0]
        positive_score = prediction_proba[1]

        # Interpretation of the score (threshold at 0.5)
        label = "Positive" if positive_score > 0.5 else "Negative"

        # Create the response
        response = {"prediction": label, "confidence_score": float(positive_score)}
        logging.info(
            f"Prediction for text '{text[:30]}...': {label} ({positive_score:.4f})"
        )
        return jsonify(response)

    except Exception:
        logging.exception("An error occurred during prediction.")
        return jsonify({"error": "An internal server error occurred."}), 500


if __name__ == "__main__":
    # For development, debug=True is fine. For production, use a WSGI server.
    # Example with Waitress: waitress-serve --host 0.0.0.0 --port 5000 app:app
    app.run(host="0.0.0.0", port=5000, debug=False)
