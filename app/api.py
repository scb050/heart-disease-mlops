from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


app = FastAPI(
    title="Heart Disease Prediction API",
    description="API para predecir riesgo de enfermedad cardiaca usando el modelo entrenado.",
    version="1.0.0"
)

MODEL_PATH = Path(__file__).resolve().parent.parent / "model.joblib"

try:
    model = joblib.load(MODEL_PATH)
    MODEL_LOADED = True
    MODEL_ERROR = None
except Exception as e:
    model = None
    MODEL_LOADED = False
    MODEL_ERROR = str(e)


class HeartInput(BaseModel):
    Age: int = Field(..., ge=18, le=100, description="Edad del paciente")
    Sex: Literal["M", "F"]
    ChestPainType: Literal["ATA", "NAP", "ASY", "TA"]
    RestingBP: int = Field(..., ge=50, le=250, description="Presion arterial en reposo")
    Cholesterol: int = Field(..., ge=0, le=700, description="Colesterol serico mg/dl")
    FastingBS: Literal[0, 1]
    RestingECG: Literal["Normal", "ST", "LVH"]
    MaxHR: int = Field(..., ge=60, le=220, description="Frecuencia cardiaca maxima")
    ExerciseAngina: Literal["Y", "N"]
    Oldpeak: float = Field(..., ge=-3.0, le=7.0)
    ST_Slope: Literal["Up", "Flat", "Down"]


class PredictionOutput(BaseModel):
    prediction: int
    probability: float
    risk_level: str


class HealthOutput(BaseModel):
    status: str
    model_loaded: bool
    model_error: str | None = None


@app.get("/health", response_model=HealthOutput)
def health():
    """Endpoint para Kubernetes readiness/liveness probes."""
    if MODEL_LOADED:
        return HealthOutput(status="ok", model_loaded=True)
    return HealthOutput(status="degraded", model_loaded=False, model_error=MODEL_ERROR)


@app.get("/", response_class=HTMLResponse)
def home():
    model_status = "Modelo cargado correctamente" if MODEL_LOADED else f"Error al cargar modelo: {MODEL_ERROR}"
    color = "green" if MODEL_LOADED else "red"
    return f"""
    <html>
        <head>
            <title>Heart Disease API</title>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f6f8; margin: 0; padding: 0; }}
                .container {{ max-width: 800px; margin: 80px auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 18px rgba(0,0,0,0.1); text-align: center; }}
                h1 {{ color: #1f4e79; margin-bottom: 10px; }}
                p {{ color: #333; font-size: 18px; line-height: 1.6; }}
                a {{ display: inline-block; margin-top: 20px; padding: 12px 20px; background-color: #1f77b4; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; }}
                a:hover {{ background-color: #155d8b; }}
                .status {{ margin-top: 25px; font-size: 16px; color: {color}; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Heart Disease Prediction API</h1>
                <p>Esta API permite predecir el riesgo de enfermedad cardiaca usando un modelo de machine learning entrenado con el dataset heart.csv.</p>
                <p>Puedes probar el endpoint de prediccion y revisar la documentacion interactiva.</p>
                <a href="/docs">Ir a la documentacion interactiva</a>
                <div class="status">{model_status}</div>
            </div>
        </body>
    </html>
    """


@app.post("/predict", response_model=PredictionOutput)
def predict(data: HeartInput):
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail=f"Modelo no disponible: {MODEL_ERROR}")

    input_df = pd.DataFrame([data.model_dump()])

    try:
        prediction = model.predict(input_df)[0]
        probability = model.predict_proba(input_df)[0, 1]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en inferencia: {str(e)}")

    if probability < 0.3:
        risk = "bajo"
    elif probability < 0.7:
        risk = "moderado"
    else:
        risk = "alto"

    return PredictionOutput(
        prediction=int(prediction),
        probability=round(float(probability), 4),
        risk_level=risk
    )
