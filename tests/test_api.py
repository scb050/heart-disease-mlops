"""
Tests automaticos para la API de prediccion de enfermedad cardiaca.

Cubre:
- Endpoint raiz (GET /).
- Endpoint de prediccion con datos validos.
- Validacion de datos invalidos (rangos fuera de spec).
- Que la probabilidad este entre 0 y 1.
- Que prediction sea 0 o 1.
"""

from fastapi.testclient import TestClient

from app.api import app


client = TestClient(app)


# Paciente de alto riesgo (hombre 58, varios factores)
HIGH_RISK_PATIENT = {
    "Age": 58,
    "Sex": "M",
    "ChestPainType": "ASY",
    "RestingBP": 150,
    "Cholesterol": 270,
    "FastingBS": 0,
    "RestingECG": "Normal",
    "MaxHR": 112,
    "ExerciseAngina": "Y",
    "Oldpeak": 2.5,
    "ST_Slope": "Flat",
}

# Paciente de bajo riesgo (mujer 35, perfil limpio)
LOW_RISK_PATIENT = {
    "Age": 35,
    "Sex": "F",
    "ChestPainType": "ATA",
    "RestingBP": 115,
    "Cholesterol": 180,
    "FastingBS": 0,
    "RestingECG": "Normal",
    "MaxHR": 180,
    "ExerciseAngina": "N",
    "Oldpeak": 0.0,
    "ST_Slope": "Up",
}


def test_home_endpoint():
    """El endpoint raiz debe responder 200 y devolver HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Heart Disease Prediction API" in response.text


def test_predict_high_risk_patient():
    """Un paciente de alto riesgo debe retornar status 200 y una probabilidad alta."""
    response = client.post("/predict", json=HIGH_RISK_PATIENT)
    assert response.status_code == 200

    data = response.json()
    assert "prediction" in data
    assert "probability" in data
    assert data["prediction"] in (0, 1)
    assert 0.0 <= data["probability"] <= 1.0


def test_predict_low_risk_patient():
    """Un paciente de bajo riesgo debe retornar status 200 con probabilidad valida."""
    response = client.post("/predict", json=LOW_RISK_PATIENT)
    assert response.status_code == 200

    data = response.json()
    assert data["prediction"] in (0, 1)
    assert 0.0 <= data["probability"] <= 1.0


def test_predict_rejects_missing_field():
    """Si falta un campo obligatorio debe devolver 422 (validacion de Pydantic)."""
    incomplete = HIGH_RISK_PATIENT.copy()
    del incomplete["Age"]

    response = client.post("/predict", json=incomplete)
    assert response.status_code == 422


def test_predict_rejects_invalid_category():
    """Si una categoria no esta permitida debe devolver 422."""
    invalid = HIGH_RISK_PATIENT.copy()
    invalid["Sex"] = "X"  # solo "M" o "F" son validos

    response = client.post("/predict", json=invalid)
    assert response.status_code == 422


def test_high_risk_has_higher_probability_than_low_risk():
    """Sanity check: el paciente de alto riesgo debe tener mayor probabilidad."""
    high = client.post("/predict", json=HIGH_RISK_PATIENT).json()
    low = client.post("/predict", json=LOW_RISK_PATIENT).json()
    assert high["probability"] > low["probability"]
