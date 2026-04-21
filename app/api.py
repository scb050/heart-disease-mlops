from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


app = FastAPI(
    title="Heart Disease Prediction API",
    description="API para predecir riesgo de enfermedad cardíaca usando el modelo entrenado.",
    version="1.0.0"
)

MODEL_PATH = Path(__file__).resolve().parent.parent / "model.joblib"
model = joblib.load(MODEL_PATH)


class HeartInput(BaseModel):
    Age: int
    Sex: Literal["M", "F"]
    ChestPainType: Literal["ATA", "NAP", "ASY", "TA"]
    RestingBP: int
    Cholesterol: int
    FastingBS: int
    RestingECG: Literal["Normal", "ST", "LVH"]
    MaxHR: int
    ExerciseAngina: Literal["Y", "N"]
    Oldpeak: float
    ST_Slope: Literal["Up", "Flat", "Down"]


class PredictionOutput(BaseModel):
    prediction: int
    probability: float


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <head>
            <title>Heart Disease API</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f4f6f8;
                    margin: 0;
                    padding: 0;
                }
                .container {
                    max-width: 800px;
                    margin: 80px auto;
                    background: white;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 4px 18px rgba(0,0,0,0.1);
                    text-align: center;
                }
                h1 {
                    color: #1f4e79;
                    margin-bottom: 10px;
                }
                p {
                    color: #333;
                    font-size: 18px;
                    line-height: 1.6;
                }
                a {
                    display: inline-block;
                    margin-top: 20px;
                    padding: 12px 20px;
                    background-color: #1f77b4;
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: bold;
                }
                a:hover {
                    background-color: #155d8b;
                }
                .status {
                    margin-top: 25px;
                    font-size: 16px;
                    color: green;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Heart Disease Prediction API</h1>
                <p>
                    Esta API permite predecir el riesgo de enfermedad cardíaca
                    usando un modelo de machine learning entrenado con el dataset heart.csv.
                </p>
                <p>
                    Puedes probar el endpoint de predicción y revisar la documentación interactiva.
                </p>
                <a href="/docs">Ir a la documentación interactiva</a>
                <div class="status">Modelo cargado correctamente</div>
            </div>
        </body>
    </html>
    """


@app.post("/predict", response_model=PredictionOutput)
def predict(data: HeartInput):
    input_df = pd.DataFrame([{
        "Age": data.Age,
        "Sex": data.Sex,
        "ChestPainType": data.ChestPainType,
        "RestingBP": data.RestingBP,
        "Cholesterol": data.Cholesterol,
        "FastingBS": data.FastingBS,
        "RestingECG": data.RestingECG,
        "MaxHR": data.MaxHR,
        "ExerciseAngina": data.ExerciseAngina,
        "Oldpeak": data.Oldpeak,
        "ST_Slope": data.ST_Slope
    }])

    prediction = model.predict(input_df)[0]
    probability = model.predict_proba(input_df)[0, 1]

    return PredictionOutput(
        prediction=int(prediction),
        probability=round(float(probability), 4)
    )
