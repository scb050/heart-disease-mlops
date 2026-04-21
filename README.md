# Heart Disease MLOps

Proyecto integrador de aprendizaje automático para predicción de enfermedad cardíaca usando el dataset `heart.csv`.

## Objetivo
Desarrollar un flujo completo de machine learning para predecir riesgo de enfermedad cardíaca, aplicando buenas prácticas de preprocesamiento, validación segura, despliegue local y monitoreo.

## Estructura del proyecto

- `app/api.py`: API con FastAPI para servir predicciones.
- `docker/`: archivos para contenerización.
- `k8s/`: archivos para despliegue local con Kubernetes.
- `notebooks/1_model_leakage_demo.ipynb`: demostración de fuga de datos.
- `notebooks/2_model_pipeline_cv.ipynb`: pipeline seguro con validación cruzada.
- `.github/workflows/ci.yml`: integración continua.
- `heart.csv`: dataset base del proyecto.
- `model.joblib`: modelo entrenado exportado.
- `drift_report.html`: reporte de monitoreo de deriva.

## Flujo del proyecto

1. Análisis inicial y demostración de data leakage.
2. Entrenamiento seguro con `Pipeline` y `GridSearchCV`.
3. Exportación del mejor modelo.
4. Despliegue con FastAPI.
5. Contenerización con Docker.
6. Despliegue local con Kubernetes.
7. Automatización con GitHub Actions.
8. Monitoreo con Evidently.

## Dataset
Se utiliza el archivo `heart.csv`, con variables clínicas para clasificación binaria de enfermedad cardíaca.

## Tecnologías
- Python
- pandas
- scikit-learn
- FastAPI
- Docker
- Kubernetes
- GitHub Actions
- Evidently
