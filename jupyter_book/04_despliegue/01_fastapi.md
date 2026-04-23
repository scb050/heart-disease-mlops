# 4.1 API REST con FastAPI

Un modelo encerrado en un `.joblib` es invisible para el resto del mundo.  Este
capítulo lo expone como un servicio HTTP con **FastAPI**, para que cualquier
cliente (una app móvil, un dashboard, otro microservicio) pueda consumirlo.

## ¿Por qué FastAPI?

- **Tipado fuerte con Pydantic** → validación automática de los JSON de entrada.
- **Documentación automática** → `/docs` (Swagger) y `/redoc` sin escribir nada.
- **Async nativo** → preparado para concurrencia.
- **Rendimiento** → Uvicorn + Starlette, comparable a Go/Node para I/O.

## Arquitectura del servicio

El archivo [`app/api.py`](../../app/api.py) implementa:

| Endpoint | Método | Propósito |
|---|---|---|
| `/` | GET | Dashboard HTML embebido para demostraciones |
| `/predict` | POST | Inferencia a partir de las 11 variables clínicas |
| `/health` | GET | Liveness probe para Kubernetes |
| `/version` | GET | Información de versión del servicio |
| `/docs` | GET | Swagger UI autogenerada |

## Carga del modelo (una sola vez)

```python
from pathlib import Path
import joblib

MODEL_PATH = Path(__file__).resolve().parent.parent / "model.joblib"

try:
    model = joblib.load(MODEL_PATH)
    MODEL_LOADED = True
    MODEL_ERROR = None
    logger.info(f"Model loaded from {MODEL_PATH}")
except Exception as exc:
    model = None
    MODEL_LOADED = False
    MODEL_ERROR = str(exc)
    logger.error(f"Failed to load model: {exc}")
```

**Decisión de diseño**: cargamos el modelo **al arrancar el proceso**, no en
cada request.  Cargar joblib es caro (decenas de ms) y no queremos pagar ese
costo en cada predicción.

Si la carga falla, guardamos el error pero **no crasheamos**.  El endpoint
`/health` lo reportará como `degraded` para que Kubernetes pueda actuar.

## Validación de entradas con Pydantic

```python
class HeartInput(BaseModel):
    Age: int = Field(..., ge=18, le=100)
    Sex: Literal["M", "F"]
    ChestPainType: Literal["ATA", "NAP", "ASY", "TA"]
    RestingBP: int = Field(..., ge=50, le=250)
    Cholesterol: int = Field(..., ge=0, le=700)
    FastingBS: Literal[0, 1]
    RestingECG: Literal["Normal", "ST", "LVH"]
    MaxHR: int = Field(..., ge=60, le=220)
    ExerciseAngina: Literal["Y", "N"]
    Oldpeak: float = Field(..., ge=-3.0, le=7.0)
    ST_Slope: Literal["Up", "Flat", "Down"]
```

Cada campo trae **rangos** y **literales** que replican las categorías que el
modelo vio en entrenamiento.  Si llega un JSON con `Sex="X"` o `Age=250`,
FastAPI responde automáticamente con **HTTP 422** y un mensaje de error claro,
**sin llegar al modelo**.

```{admonition} Por qué esto es importante
:class: tip

El modelo fue entrenado con categorías específicas.  Si recibe una no vista,
`OneHotEncoder(handle_unknown='ignore')` la codifica como todos ceros y la
predicción se degrada silenciosamente.  Mejor rechazarla temprano, en la capa
de API.
```

## Lógica del endpoint `/predict`

```python
@app.post("/predict", response_model=PredictionOutput, tags=["inference"])
def predict(data: HeartInput):
    """Inferencia de riesgo cardiovascular a partir de variables clínicas."""
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail=f"Modelo no disponible: {MODEL_ERROR}")

    # Convertimos el JSON validado a DataFrame para que el pipeline
    # reconozca las columnas por nombre.
    input_df = pd.DataFrame([data.model_dump()])

    try:
        prediction = int(model.predict(input_df)[0])
        probability = float(model.predict_proba(input_df)[0, 1])
    except Exception as exc:
        logger.exception("Inference failed")
        raise HTTPException(status_code=500, detail=f"Error en inferencia: {exc}")

    # Traducción de probabilidad a nivel de riesgo legible.
    if probability < 0.3:
        risk = "bajo"
    elif probability < 0.7:
        risk = "moderado"
    else:
        risk = "alto"

    return PredictionOutput(
        prediction=prediction,
        probability=round(probability, 4),
        risk_level=risk,
        model_version=API_VERSION,
    )
```

### Qué hace cada bloque

1. **Guarda de disponibilidad** → si el modelo no cargó, devuelve `503` en vez
   de fallar feo.
2. **JSON → DataFrame** → imprescindible porque el `ColumnTransformer` necesita
   las columnas con nombre.
3. **Predicción + probabilidad** → con try/except porque cualquier error raro
   se traduce a un `500` limpio con log.
4. **Nivel de riesgo** → convierte la probabilidad en algo que un humano
   entiende (`bajo`/`moderado`/`alto`).
5. **Respuesta tipada** → el `PredictionOutput` garantiza el contrato de salida.

## Middleware y observabilidad

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} "
        f"({elapsed_ms:.1f} ms)"
    )
    return response
```

Cada request deja un log estructurado con método, path, status y latencia.  En
producción este log alimentaría herramientas como Grafana Loki o Datadog.

## Dashboard embebido

La ruta `/` sirve una **página HTML autocontenida** (unos 600 líneas dentro de
`api.py`) que permite probar el modelo en el navegador sin frontend externo.
Es útil para demos y para validaciones manuales rápidas.

## Cómo levantarla en local

```bash
# Instalar dependencias
pip install -r docker/requirements.txt

# Arrancar el servidor
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

Y después:

- `http://localhost:8000/` → dashboard.
- `http://localhost:8000/docs` → Swagger.
- `http://localhost:8000/predict` → el endpoint real.
