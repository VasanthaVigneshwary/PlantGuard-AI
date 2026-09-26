from fastapi.testclient import TestClient

from main import app
from routes import plant

client = TestClient(app)


def test_chat_accepts_tamil_language_and_responds_in_tamil(monkeypatch):
    monkeypatch.setattr(
        plant,
        "get_disease_details",
        lambda disease_id: {
            "disease": (1, "Tomato Late Blight", "Tomato", "Late blight disease description"),
            "symptoms": [(1, "Dark leaf lesions", "Leaf lesions appear on leaves"), (2, "Fruit lesions", "Fruit rot may occur")],
            "causes": [(1, "Humidity", "Humidity is high")],
            "treatments": [(1, "Copper fungicide", "Fungicide", "Treat with proper fungicide", "Use as directed", "Wear protection", [(1, "Foliar spray", "L/acre", 1.5, "acre", "Apply as needed")])],
            "prevention": [(1, "Good air circulation", "Improve spacing")],
        },
    )

    response = client.post(
        "/api/chat",
        json={
            "message": "இந்த நோயின் அறிகுறிகள் என்ன?",
            "crop": "Tomato",
            "disease": "Tomato Late Blight",
            "confidence": 9.37,
            "disease_id": 1,
            "language": "ta",
        },
    )

    assert response.status_code == 200
    assert "அறிகுறிகள்" in response.json()["response"]


def test_chat_defaults_to_english_for_unsupported_language(monkeypatch):
    monkeypatch.setattr(
        plant,
        "get_disease_details",
        lambda disease_id: {
            "disease": (1, "Tomato Late Blight", "Tomato", "Late blight disease description"),
            "symptoms": [(1, "Dark leaf lesions", "Leaf lesions appear on leaves")],
            "causes": [(1, "Humidity", "Humidity is high")],
            "treatments": [(1, "Copper fungicide", "Fungicide", "Treat with proper fungicide", "Use as directed", "Wear protection", [(1, "Foliar spray", "L/acre", 1.5, "acre", "Apply as needed")])],
            "prevention": [(1, "Good air circulation", "Improve spacing")],
        },
    )

    response = client.post(
        "/api/chat",
        json={
            "message": "What are the symptoms?",
            "crop": "Tomato",
            "disease": "Tomato Late Blight",
            "confidence": 9.37,
            "disease_id": 1,
            "language": "fr",
        },
    )

    assert response.status_code == 200
    assert "symptoms" in response.json()["response"].lower()


def test_upload_localizes_dynamic_explanation_for_tamil(monkeypatch):
    monkeypatch.setattr(
        plant,
        "predict_disease",
        lambda file_path: {
            "disease": "tomato___late_blight",
            "confidence": 42.5,
            "status": "predicted",
        },
    )

    monkeypatch.setattr(
        plant,
        "get_disease_details_by_prediction",
        lambda prediction: {
            "disease": (1, "Tomato Late Blight", "Tomato", "Late blight can spread quickly under cool and humid conditions. Early observation and proper plant care can help reduce further spread."),
            "symptoms": [(1, "Dark leaf lesions", "Leaf lesions appear on leaves"), (2, "Fruit lesions", "Fruit rot may occur")],
            "causes": [(1, "High humidity", "High humidity favors spread")],
            "treatments": [(1, "Copper fungicide", "Fungicide", "Treat with proper fungicide", "Use as directed", "Wear protection", [(1, "Foliar spray", "L/acre", 1.5, "acre", "Source: TNAU Agritech Portal. Verify current product label and local approval before use.")])],
            "prevention": [(1, "Good air circulation", "Improve spacing")],
        },
    )

    response = client.post(
        "/api/upload",
        files={"file": ("leaf.jpg", b"fake-image-data", "image/jpeg")},
        data={"language": "ta"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "குளிர்ச்சியான" in payload["disease"]["description"]
    assert "இலைகளில்" in payload["symptoms"][0]["name"]
    assert "காரணம்" in payload["causes"][0]["name"] or "அதிக ஈரப்பதம்" in payload["causes"][0]["name"]
    assert "அறிவுறுத்தல்கள்" in payload["treatments"][0]["instructions"] or "வழிமுறைகள்" in payload["treatments"][0]["instructions"]
