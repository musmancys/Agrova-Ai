import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import io
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app, CropAnalysisResponse, AgronomistResponse

client = TestClient(app)


def test_health_check():
    """Verify that the health check endpoint returns 200 and system details."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Agrova AI Backend"
    assert data["model"] == "gemini-3.6-flash"


def test_serve_frontend():
    """Verify that the root endpoint serves the HTML frontend."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Agrova · AI for Farmers" in response.text
    assert "Scan Your Crop" in response.text


def test_get_weather_live_or_fallback():
    """Verify that the weather endpoint returns expected fields."""
    response = client.get("/api/weather?lat=31.5497&lon=74.3436")
    assert response.status_code == 200
    data = response.json()
    assert "temperature" in data
    assert "humidity" in data
    assert "rain_chance" in data
    assert "location" in data
    assert "°C" in data["temperature"]
    assert "%" in data["humidity"]
    assert "%" in data["rain_chance"]
    assert data["location"] == "Punjab, PK"


def test_ask_agronomist_validation_error():
    """Verify that invalid/empty input triggers a 422 validation error."""
    response = client.post("/api/ask-agronomist", json={"question": ""})
    assert response.status_code == 422


@patch("main.get_gemini_client")
def test_ask_agronomist_success(mock_get_client):
    """Verify that a valid agronomy query receives a properly structured response."""
    mock_gemini = MagicMock()
    mock_response = MagicMock()
    mock_response.text = (
        "Your tomato leaves may be infected with Early Blight. "
        "Remove damaged leaves, avoid overhead watering, and apply a copper fungicide."
    )
    mock_gemini.models.generate_content.return_value = mock_response
    mock_get_client.return_value = mock_gemini

    payload = {"question": "My tomato leaves have brown spots, what should I spray?"}
    response = client.post("/api/ask-agronomist", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "Early Blight" in data["response"]


def test_analyze_crop_invalid_file_type():
    """Verify that uploading a non-image file returns 400 Bad Request."""
    fake_file = io.BytesIO(b"not an image file")
    response = client.post(
        "/api/analyze-crop",
        files={"file": ("notes.txt", fake_file, "text/plain")}
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


@patch("main.get_gemini_client")
def test_analyze_crop_success(mock_get_client):
    """Verify multimodal crop analysis returns the required structured diagnostic schema."""
    mock_gemini = MagicMock()
    mock_response = MagicMock()
    mock_response.text = """
    {
      "crop_name": "Tomato",
      "disease_name": "Early Blight",
      "confidence": "94%",
      "severity": "Moderate",
      "recommendations": [
        "Remove heavily infected leaves",
        "Avoid overhead watering",
        "Apply recommended copper-based fungicide"
      ],
      "weather_alert": "High humidity detected; avoid evening irrigation."
    }
    """
    mock_gemini.models.generate_content.return_value = mock_response
    mock_get_client.return_value = mock_gemini

    fake_image = io.BytesIO(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00")
    response = client.post(
        "/api/analyze-crop",
        files={"file": ("leaf.jpg", fake_image, "image/jpeg")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["crop_name"] == "Tomato"
    assert data["disease_name"] == "Early Blight"
    assert data["confidence"] == "94%"
    assert data["severity"] == "Moderate"
    assert len(data["recommendations"]) == 3
    assert "High humidity" in data["weather_alert"]
