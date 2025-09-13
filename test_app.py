import pytest
from app import app as flask_app


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
    assert response.json == {"status": "ok"}

def test_predict_missing_text(client):
    """Test the /predict endpoint with no text provided, expecting a 400 error."""
    response = client.post("/predict", json={})
    assert response.status_code == 400
    assert response.json == {"error": 'The "text" field is missing.'}


def test_predict_success(client):
    """Test the /predict endpoint with valid text, expecting a 200 OK response."""
    response = client.post("/predict", json={"text": "this is a wonderful movie"})
    assert response.status_code == 200
    json_data = response.json
    assert "prediction" in json_data
    assert "confidence_score" in json_data
    assert json_data["prediction"] in ["Positive", "Negative"]
