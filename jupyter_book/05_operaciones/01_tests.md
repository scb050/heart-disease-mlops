# 5.1 Tests automáticos de la API

Un servicio que no tiene tests es un servicio que **no sabe que está roto**.
En este capítulo escribimos tests para la API con `pytest` y el `TestClient`
de FastAPI.

## ¿Qué cubrimos?

El archivo [`tests/test_api.py`](../../tests/test_api.py) cubre siete casos:

| Test | Qué valida |
|---|---|
| `test_home_endpoint` | El dashboard HTML responde 200 y contiene el título. |
| `test_predict_high_risk_patient` | Un paciente de alto riesgo recibe una respuesta válida. |
| `test_predict_low_risk_patient` | Un paciente de bajo riesgo recibe una respuesta válida. |
| `test_predict_rejects_missing_field` | Si falta `Age`, la API responde 422. |
| `test_predict_rejects_invalid_category` | Si `Sex="X"`, la API responde 422. |
| `test_high_risk_has_higher_probability_than_low_risk` | Sanity check semántico. |
| `test_health_endpoint` | `/health` responde `ok` y `model_loaded=True`. |
| `test_version_endpoint` | `/version` expone la versión correcta. |

## TestClient: cómo funciona

```python
from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)
```

El `TestClient` **no levanta un servidor real** — habla con la app en memoria
a través de la interfaz WSGI/ASGI.  Ventajas:

- Sin puertos ni threads → tests rápidos y deterministas.
- Sin mocks de HTTP → valida la misma lógica que veremos en producción.
- Corre en CI sin infraestructura adicional.

## Dos pacientes de referencia

```python
HIGH_RISK_PATIENT = {
    "Age": 58, "Sex": "M", "ChestPainType": "ASY",
    "RestingBP": 150, "Cholesterol": 270,
    "FastingBS": 0, "RestingECG": "Normal",
    "MaxHR": 112, "ExerciseAngina": "Y",
    "Oldpeak": 2.5, "ST_Slope": "Flat",
}

LOW_RISK_PATIENT = {
    "Age": 35, "Sex": "F", "ChestPainType": "ATA",
    "RestingBP": 115, "Cholesterol": 180,
    "FastingBS": 0, "RestingECG": "Normal",
    "MaxHR": 180, "ExerciseAngina": "N",
    "Oldpeak": 0.0, "ST_Slope": "Up",
}
```

Elegimos **dos perfiles opuestos** que el modelo debería poder distinguir
claramente.  Esto nos permite escribir un test de "sanidad semántica":

```python
def test_high_risk_has_higher_probability_than_low_risk():
    high = client.post("/predict", json=HIGH_RISK_PATIENT).json()
    low = client.post("/predict", json=LOW_RISK_PATIENT).json()
    assert high["probability"] > low["probability"]
```

Este test es oro puro.  **No verifica un número exacto** (que cambiaría al
reentrenar el modelo), pero sí que el modelo **ordena** correctamente los
extremos del espectro de riesgo.

## Tests de validación de entrada

```python
def test_predict_rejects_missing_field():
    incomplete = HIGH_RISK_PATIENT.copy()
    del incomplete["Age"]
    response = client.post("/predict", json=incomplete)
    assert response.status_code == 422

def test_predict_rejects_invalid_category():
    invalid = HIGH_RISK_PATIENT.copy()
    invalid["Sex"] = "X"
    response = client.post("/predict", json=invalid)
    assert response.status_code == 422
```

Estos son en realidad **tests de Pydantic** — validan que los tipos y
restricciones declarados en `HeartInput` funcionan.  Si alguien "relaja" la
validación sin querer, el test lo detecta.

## Tests del contrato de respuesta

```python
def test_predict_high_risk_patient():
    response = client.post("/predict", json=HIGH_RISK_PATIENT)
    assert response.status_code == 200

    data = response.json()
    assert "prediction" in data
    assert "probability" in data
    assert data["prediction"] in (0, 1)
    assert 0.0 <= data["probability"] <= 1.0
```

Aquí validamos tres cosas del contrato:

1. El **status HTTP** es 200.
2. Las **claves** esperadas están presentes.
3. Los **rangos** son válidos (`prediction` es binaria, `probability` ∈ [0, 1]).

## Cómo ejecutar los tests

```bash
# Instalar dependencias de desarrollo
pip install -r tests/requirements-dev.txt

# Ejecutar toda la suite
pytest tests/ -v

# Ejecutar sólo un test
pytest tests/test_api.py::test_health_endpoint -v
```

## Filosofía aplicada

```{admonition} Tests que valen la pena
:class: tip

Los tests escritos aquí siguen tres principios:

1. **Determinísticos** — mismo input, mismo resultado.
2. **Independientes del modelo** — no fallan si cambiamos el estimador, siempre
   que la API siga funcionando correctamente.
3. **Legibles** — cualquiera que lea el test entiende qué se está probando
   **y por qué**.
```
