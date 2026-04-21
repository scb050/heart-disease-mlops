from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI
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


@app.get("/")
def home():
    return {
        "message": "Heart Disease Prediction API is running",
        "model_loaded": MODEL_PATH.exists()
    }


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
