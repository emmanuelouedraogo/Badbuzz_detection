# /full/path/to/your/project/badbuzz_detection/app.py
# Set TensorFlow log level before any other imports.
# 0 = all messages, 1 = filter INFO, 2 = filter WARNING, 3 = filter ERROR
import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import logging
from flask import Flask, request, jsonify
import joblib  # Utiliser joblib pour charger le pipeline scikit-learn

# --- Configuration & Logging ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Constants ---
# Chemin vers le pipeline sauvegardé
PIPELINE_PATH = "pipeline.joblib"


# --- Flask App Initialization ---
app = Flask(__name__)  # Create the Flask app instance


# --- Global variables for model and vectorizer ---
pipeline = None


def load_pipeline():
    """Charge le pipeline Scikit-learn depuis le disque."""
    global pipeline
    try:
        logging.info("Chargement du pipeline Scikit-learn...")
        pipeline = joblib.load(PIPELINE_PATH)
        logging.info("Pipeline chargé avec succès.")

        # Add type checks to ensure the loaded objects are correct
        if not hasattr(pipeline, "predict_proba"):
            raise TypeError(
                "L'objet 'pipeline' chargé n'est pas un pipeline Scikit-learn valide."
            )
    except Exception as e:
        logging.error(f"Erreur lors du chargement du pipeline : {e}")
        raise


# --- Load resources and perform a warm-up at startup ---
if not app.config.get("TESTING"):
    try:
        load_pipeline()
        logging.info("Exécution d'une prédiction de chauffe...")
        warmup_text = "Ceci est un texte de test."
        if not hasattr(pipeline, "predict_proba"):
            raise TypeError(
                "L'objet Pipeline est invalide et n'a pas de méthode 'predict_proba'."
            )
        # Le pipeline gère la vectorisation et la prédiction
        pipeline.predict_proba([warmup_text])
        logging.info("Prédiction de chauffe réussie. L'API est prête.")
    except Exception as e:
        logging.critical(
            f"Le démarrage de l'application a échoué pendant la chauffe : {e}"
        )
        raise


@app.route("/", methods=["GET"])
def index():
    """Root endpoint to provide a simple status message."""
    return jsonify({"message": "Bad Buzz Detection API is running."}), 200


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to confirm the service is running."""
    return jsonify({"status": "ok"}), 200


@app.route("/predict", methods=["POST"])
def predict():
    """
    Analyse le sentiment du texte fourni en utilisant le pipeline chargé.
    """
    try:
        data = request.get_json(force=True)
        text = data.get("text", "")

        if not text:
            logging.warning("Requête de prédiction reçue sans champ 'text'.")
            return jsonify({"error": "Le champ 'text' est manquant."}), 400

        # Le pipeline gère à la fois le pré-traitement (TF-IDF) et la prédiction
        prediction_proba = pipeline.predict_proba([text])[0]

        # Le modèle a été entraîné avec 0=Négatif, 1=Positif.
        # predict_proba renvoie [[P(neg), P(pos)]].
        positive_score = prediction_proba[1]

        # Interprétation du score (seuil à 0.5)
        label = "Positive" if positive_score > 0.5 else "Negative"

        # Création de la réponse
        logging.info(
            f"Prédiction pour le texte '{text[:30]}...': {label} (score: {positive_score:.4f})"
        )
        return jsonify({"prediction": label, "confidence_score": float(positive_score)})

    except Exception as e:
        logging.exception(f"Une erreur est survenue pendant la prédiction : {e}")
        return jsonify({"error": "Une erreur interne est survenue."}), 500


if __name__ == "__main__":
    # Utiliser le serveur de production Waitress pour la stabilité.
    from waitress import serve

    serve(app, host="0.0.0.0", port=5000)
