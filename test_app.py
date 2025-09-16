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
    """Fixture to mock a model that predicts 'Positive'."""
    mock_model = Mock()
    mock_model.predict_proba.return_value = np.array(
        [[0.1, 0.9]]
    )  # High positive score
    mock_vectorizer = Mock()
    monkeypatch.setattr("app.model", mock_model)
    monkeypatch.setattr("app.vectorizer", mock_vectorizer)


@pytest.fixture
def mock_negative_model(monkeypatch):
    """Fixture to mock a model that predicts 'Negative'."""
    mock_model = Mock()
    mock_model.predict_proba.return_value = np.array([[0.9, 0.1]])  # Low positive score
    mock_vectorizer = Mock()
    monkeypatch.setattr("app.model", mock_model)
    monkeypatch.setattr("app.vectorizer", mock_vectorizer)


def test_predict_positive(client, mock_positive_model):
    """Test the /predict endpoint for a positive sentiment prediction."""
    response = client.post(
        "/predict",
        data=json.dumps({"text": "This is great!"}),
        content_type="application/json",
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["prediction"] == "Positive"


def test_predict_negative(client, mock_negative_model):
    """Test the /predict endpoint for a negative sentiment prediction."""
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
    # We only need to mock the vectorizer, as the model won't be called
    # if the text is empty.
    mock_vectorizer = Mock()
    monkeypatch.setattr("app.vectorizer", mock_vectorizer)
    response = client.post("/predict", json={})
    assert response.status_code == 400
    assert response.json == {"error": 'The "text" field is missing.'}
