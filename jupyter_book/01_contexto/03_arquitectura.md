# 1.3 Arquitectura del proyecto

Una manera útil de entender el proyecto es mirar cómo **fluye la información**
desde los datos crudos hasta una predicción consumida por el usuario final.

## Diagrama de alto nivel

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│  heart.csv  │ ──▶ │  Notebook 2      │ ──▶ │ model.joblib │
│  (dataset)  │     │  Pipeline + CV   │     │ (artefacto)  │
└─────────────┘     └──────────────────┘     └──────┬───────┘
                                                    │
                                                    ▼
                            ┌────────────────────────────────────┐
                            │  FastAPI  (app/api.py)             │
                            │   - /predict                       │
                            │   - /health  /version              │
                            │   - Dashboard HTML en  /           │
                            └──────────────┬─────────────────────┘
                                           │
                          ┌────────────────┴────────────────┐
                          ▼                                 ▼
                 ┌────────────────┐              ┌────────────────────┐
                 │ Docker image   │              │  Tests (pytest)    │
                 │ heart-api      │              │  + GitHub Actions  │
                 └───────┬────────┘              └────────────────────┘
                         │
                         ▼
                 ┌────────────────┐              ┌────────────────────┐
                 │ Kubernetes     │   ◀───────── │  Evidently drift   │
                 │ deployment +   │              │  report (HTML)     │
                 │ service        │              └────────────────────┘
                 └────────────────┘
```

## Organización de carpetas

```
heart-disease-mlops/
├── heart.csv                  # Dataset base
├── model.joblib               # Modelo entrenado (exportado)
├── environment.yml            # Entorno conda reproducible
├── drift_report.html          # Reporte de drift generado por Evidently
│
├── notebooks/
│   ├── 1_model_leakage_demo.ipynb   # Demostración de fuga de datos
│   └── 2_model_pipeline_cv.ipynb    # Pipeline seguro + GridSearchCV
│
├── app/
│   └── api.py                 # FastAPI (endpoints + dashboard HTML)
│
├── docker/
│   ├── Dockerfile             # Imagen de la API
│   └── requirements.txt       # Dependencias del servicio
│
├── k8s/
│   ├── deployment.yaml        # Pod de Kubernetes
│   └── service.yaml           # LoadBalancer
│
├── tests/
│   ├── test_api.py            # Tests automáticos de la API
│   └── requirements-dev.txt
│
├── monitoring/
│   ├── generate_drift_report.py
│   ├── Dockerfile.monitoring
│   └── requirements-monitoring.txt
│
└── .github/workflows/ci.yml   # Integración continua
```

## Capas del sistema

| Capa | Qué hace | Tecnologías |
|---|---|---|
| **Datos** | Almacena el dataset base y el modelo entrenado | `heart.csv`, `model.joblib` |
| **Entrenamiento** | Limpia, preprocesa, entrena y valida | pandas, scikit-learn |
| **Servicio** | Expone el modelo vía HTTP | FastAPI, Pydantic |
| **Empaquetado** | Imagen inmutable reproducible | Docker |
| **Orquestación** | Gestiona réplicas, red y disponibilidad | Kubernetes |
| **Calidad** | Verifica que nada se rompió | pytest, GitHub Actions |
| **Observabilidad** | Detecta drift en los datos de entrada | Evidently |

```{admonition} Principio guía
:class: important

Cada capa **no conoce los detalles internos** de las otras.  El modelo no sabe
quién lo está consumiendo, la API no sabe cómo se entrenó, y Kubernetes sólo sabe
que hay una imagen Docker que expone el puerto 8000.  Esto se llama
**desacoplamiento** y es la razón por la que se puede cambiar cualquier pieza sin
romper el resto.
```
