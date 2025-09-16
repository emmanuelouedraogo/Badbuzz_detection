import json
import pytest
import numpy as np
from app import app as flask_app, load_resources  # Import the app and loader


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # You can add test-specific configuration here if needed
    yield flask_app


@pytest.fixture
def client(app):
    """A test client for the app."""
    # Eagerly load model and tokenizer for testing purposes to avoid errors
    # with lazy loading in the test environment.
    with app.app_context():
        load_resources()
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


def test_predict_positive(client, monkeypatch):
    """Test the /predict endpoint for a positive sentiment prediction."""

    # Mock the model's predict method to return a low score (positive)
    def mock_predict(*args, **kwargs):
        return np.array([[0.1]])  # Score < 0.5 -> Positive

    monkeypatch.setattr("app.model.predict", mock_predict)

    response = client.post(
        "/predict",
        data=json.dumps({"text": "This is great!"}),
        content_type="application/json",
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["prediction"] == "Positive"


def test_predict_negative(client, monkeypatch):
    """Test the /predict endpoint for a negative sentiment prediction."""

    # Mock the model's predict method to return a high score (negative)
    def mock_predict(*args, **kwargs):
        return np.array([[0.9]])  # Score > 0.5 -> Negative

    monkeypatch.setattr("app.model.predict", mock_predict)

    response = client.post(
        "/predict",
        data=json.dumps({"text": "This is awful."}),
        content_type="application/json",
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["prediction"] == "Negative"


def test_predict_no_text(client, monkeypatch):
    """Test the /predict endpoint when no text is provided."""
    # Mock the model to avoid loading it for this simple validation test.
    monkeypatch.setattr("app.model", "mock_model")
    response = client.post("/predict", json={})
    assert response.status_code == 400
    assert response.json == {"error": 'The "text" field is missing.'}
