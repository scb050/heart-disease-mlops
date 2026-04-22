"""
Monitoreo de deriva de datos con Evidently.

Este script simula un escenario real de monitoreo en produccion:
- reference: datos con los que se entreno el modelo (muestra del heart.csv).
- current: datos que "llegan en produccion" (otra muestra con drift simulado).

Genera un reporte HTML con el analisis de drift columna por columna.
"""

import numpy as np
import pandas as pd

from evidently import Report
from evidently.presets import DataDriftPreset, DataSummaryPreset


import os

RANDOM_STATE = 42
INPUT_CSV = os.environ.get("INPUT_CSV", "heart.csv")
OUTPUT_HTML = os.environ.get("OUTPUT_HTML", "drift_report.html")


def load_and_split_data(path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carga el dataset y lo divide en dos muestras: referencia y actual."""
    df = pd.read_csv(path)
    df_shuffled = df.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)

    cut = len(df_shuffled) // 2
    reference = df_shuffled.iloc[:cut].copy()
    current = df_shuffled.iloc[cut:].copy()

    return reference, current


def simulate_drift(current: pd.DataFrame) -> pd.DataFrame:
    """
    Simula drift en los datos actuales para que el reporte tenga algo que mostrar.

    Esto imita lo que pasaria en produccion real:
    - La poblacion de pacientes envejece un poco.
    - El colesterol promedio sube (cambio de habitos alimenticios).
    - La frecuencia cardiaca maxima baja (poblacion menos activa).
    - Cambia la distribucion del tipo de dolor de pecho.
    """
    current = current.copy()
    rng = np.random.default_rng(RANDOM_STATE)

    current["Age"] = current["Age"] + rng.integers(2, 8, size=len(current))
    current["Cholesterol"] = current["Cholesterol"] + rng.integers(15, 40, size=len(current))
    current["MaxHR"] = current["MaxHR"] - rng.integers(5, 20, size=len(current))

    # Forzar un cambio en la distribucion de una variable categorica
    mask = rng.random(len(current)) < 0.25
    current.loc[mask, "ChestPainType"] = "ASY"

    return current


def generate_report(reference: pd.DataFrame, current: pd.DataFrame, output_path: str) -> None:
    """Crea el reporte de drift y lo guarda como HTML."""
    report = Report(metrics=[
        DataDriftPreset(),
        DataSummaryPreset(),
    ])

    snapshot = report.run(reference_data=reference, current_data=current)
    snapshot.save_html(output_path)

    print(f"Reporte generado en: {output_path}")
    print(f"Filas referencia: {len(reference)}")
    print(f"Filas actual:     {len(current)}")


def main() -> None:
    print("=== Generando reporte de drift con Evidently ===")
    reference, current = load_and_split_data(INPUT_CSV)
    current = simulate_drift(current)
    generate_report(reference, current, OUTPUT_HTML)
    print("Listo.")


if __name__ == "__main__":
    main()
