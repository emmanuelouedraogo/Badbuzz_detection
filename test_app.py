import json
import pytest
import numpy as np
from unittest.mock import Mock
from app import app as flask_app


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # You can add test-specific configuration here if needed
    yield flask_app


@pytest.fixture
def client(app):
    """A test client for the app."""
    # We don't call load_resources() here anymore because our tests
    # will mock the model and vectorizer directly.
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Test the /health endpoint to ensure the API is responsive."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_root_endpoint(client):
    """Test the root endpoint to ensure it's available."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json


@pytest.fixture
def mock_positive_model(monkeypatch):
    """Fixture pour simuler un pipeline qui prédit 'Positif'."""
    mock_pipeline = Mock()
    mock_pipeline.predict_proba.return_value = np.array(
        [[0.1, 0.9]]
    )  # Score positif élevé
    monkeypatch.setattr("app.pipeline", mock_pipeline)


@pytest.fixture
def mock_negative_model(monkeypatch):
    """Fixture pour simuler un pipeline qui prédit 'Négatif'."""
    mock_pipeline = Mock()
    mock_pipeline.predict_proba.return_value = np.array(
        [[0.9, 0.1]]
    )  # Score positif bas
    monkeypatch.setattr("app.pipeline", mock_pipeline)


def test_predict_positive(client, mock_positive_model):
    """Test the /predict endpoint for a positive sentiment prediction."""
    response = client.post(
        "/predict",
        json={"text": "This is great!"},
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["prediction"] == "Positive"


def test_predict_negative(client, mock_negative_model):
    """Test the /predict endpoint for a negative sentiment prediction."""
    response = client.post(
        "/predict",
        json={"text": "This is awful."},
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["prediction"] == "Negative"


def test_predict_no_text(client):
    """Test the /predict endpoint when no text is provided."""
    # Pas besoin de mock, la validation se fait avant l'appel au pipeline.
    response = client.post("/predict", json={})
    assert response.status_code == 400
    assert response.json == {"error": "Le champ 'text' est manquant."}
