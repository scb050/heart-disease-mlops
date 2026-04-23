# 5.2 Monitoreo de data drift con Evidently

Una vez desplegado, el modelo no está "terminado".  Los pacientes cambian con
el tiempo, los protocolos clínicos evolucionan, las escalas de medición se
actualizan.  Si el modelo sigue prediciendo con datos que **ya no se parecen**
a los de entrenamiento, su calidad se degrada en silencio.  Esto se llama
**data drift**.

## El script [`monitoring/generate_drift_report.py`](../../monitoring/generate_drift_report.py)

Simula un escenario de producción y genera un reporte HTML con **Evidently**.

### Decisiones del script

```python
RANDOM_STATE = 42
INPUT_CSV = os.environ.get("INPUT_CSV", "heart.csv")
OUTPUT_HTML = os.environ.get("OUTPUT_HTML", "drift_report.html")
```

Parametrizamos por **variables de entorno** para que el mismo script corra
igual en local y en un contenedor (Dockerfile.monitoring en el mismo folder).

### Paso 1 · Split de referencia vs. actual

```python
def load_and_split_data(path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carga el dataset y lo divide en dos muestras: referencia y actual."""
    df = pd.read_csv(path)
    df_shuffled = df.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)

    cut = len(df_shuffled) // 2
    reference = df_shuffled.iloc[:cut].copy()
    current = df_shuffled.iloc[cut:].copy()

    return reference, current
```

- **`reference`** → "lo que el modelo vio al entrenar".
- **`current`** → "lo que está llegando ahora en producción".

Shuffle con `random_state=42` para reproducibilidad.

### Paso 2 · Simulación explícita de drift

```python
def simulate_drift(current: pd.DataFrame) -> pd.DataFrame:
    current = current.copy()
    rng = np.random.default_rng(RANDOM_STATE)

    current["Age"] = current["Age"] + rng.integers(2, 8, size=len(current))
    current["Cholesterol"] = current["Cholesterol"] + rng.integers(15, 40, size=len(current))
    current["MaxHR"] = current["MaxHR"] - rng.integers(5, 20, size=len(current))

    mask = rng.random(len(current)) < 0.25
    current.loc[mask, "ChestPainType"] = "ASY"

    return current
```

Introducimos **cambios realistas** para que el reporte tenga algo que mostrar:

| Variable | Qué simulamos | Por qué tiene sentido clínico |
|---|---|---|
| `Age` | +2 a +8 años | La población envejece. |
| `Cholesterol` | +15 a +40 mg/dl | Cambios de alimentación. |
| `MaxHR` | –5 a –20 bpm | Población menos activa. |
| `ChestPainType` | 25 % a `ASY` | Cambio en clasificación. |

Esta función es **pedagógica**; en producción no se simula nada, simplemente se
pasa el snapshot real del día, semana o mes.

### Paso 3 · Generar el reporte

```python
from evidently import Report
from evidently.presets import DataDriftPreset, DataSummaryPreset

def generate_report(reference, current, output_path):
    report = Report(metrics=[
        DataDriftPreset(),
        DataSummaryPreset(),
    ])

    snapshot = report.run(reference_data=reference, current_data=current)
    snapshot.save_html(output_path)
```

- **`DataDriftPreset`** → compara distribuciones columna por columna con tests
  estadísticos (Kolmogorov–Smirnov para numéricas, chi-cuadrado para
  categóricas).
- **`DataSummaryPreset`** → estadísticas descriptivas (media, desviación,
  percentiles) de ambos conjuntos.

El reporte se guarda como HTML **autocontenido** — se puede abrir en cualquier
navegador sin dependencias externas.  Ya está en la raíz del proyecto como
[`drift_report.html`](../../drift_report.html).

## Ejecución

```bash
# En local
python monitoring/generate_drift_report.py

# Dentro del container (desde la raíz)
docker build -f monitoring/Dockerfile.monitoring -t heart-drift .
docker run -v $(pwd):/data heart-drift
```

## Qué mirar en el reporte

1. **Columna por columna** → ¿cuáles variables driftearon?
2. **Magnitud del drift** → ¿es un cambio menor o estructural?
3. **Significancia estadística** → el test estadístico da un `p-value`.  Por
   debajo de 0.05 suele considerarse drift real.
4. **Nivel global** → ¿cuántas variables pasaron el umbral de drift?

```{admonition} Interpretación clínica
:class: important

Detectar drift **no significa automáticamente** que el modelo falla.  Significa
que las condiciones del dato cambiaron.  El siguiente paso correcto es:

1. Confirmar con el equipo clínico si el cambio es esperado.
2. Medir el **performance drift** (usando etiquetas reales si hay).
3. Decidir si hay que **reentrenar** el modelo con datos recientes.
```

## Cómo integrar esto en un flujo real

| Frecuencia | Qué hacer |
|---|---|
| **Diario** | Generar reporte de drift sobre los últimos N días. |
| **Semanal** | Calcular performance real (AUC) si hay etiquetas nuevas. |
| **Mensual** | Decidir si reentrenar. |
| **Evento** | Cualquier cambio mayor dispara una revisión inmediata. |

El script de este proyecto es la **base** sobre la que se puede construir un
pipeline automatizado con Airflow, Prefect o GitHub Actions programadas.
