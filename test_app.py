import json
import pytest
import numpy as np
from app import app as flask_app  # Import the app from your file


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    # This setup will load the app context, including models.
    # For faster tests in the future, consider an app factory pattern.
    with flask_app.test_client() as client:
        yield client


def test_health_check(client):
    """Test the /health endpoint to ensure the API is responsive."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "healthy"}


def test_predict_no_text(client):
    """Test the /predict endpoint with no text provided, expecting a 400 error."""
    response = client.post("/predict", json={})
    assert response.status_code == 400
    assert response.json == {"error": 'The "text" field is missing.'}


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
