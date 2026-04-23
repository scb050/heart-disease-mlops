# Heart Disease MLOps

```{admonition} Proyecto integrador de Machine Learning + MLOps
:class: tip

Este libro documenta el ciclo completo de un proyecto de *machine learning aplicado*
a la predicción de **enfermedad cardiovascular**, desde el análisis del dataset hasta
el despliegue del modelo como servicio web y su posterior **monitoreo en producción**.
```

## ¿Qué vas a encontrar?

Este libro está organizado como un recorrido práctico por todas las etapas de un
proyecto real de MLOps:

1. **Contexto** — Qué problema se resuelve, qué datos se usan y cómo está armada la
   arquitectura del proyecto.
2. **Análisis y fuga de datos** — Una demostración intencional de *data leakage* para
   entender por qué es peligroso y cómo evitarlo.
3. **Pipeline seguro** — Construcción de un pipeline de scikit-learn con
   `ColumnTransformer` + `GridSearchCV` que elimina la fuga y compara varios modelos.
4. **Despliegue** — Exposición del modelo como API REST con FastAPI, contenerización
   con Docker y despliegue local con Kubernetes.
5. **Operación y monitoreo** — Tests automáticos, integración continua con GitHub
   Actions y monitoreo de *data drift* con Evidently.
6. **Conclusiones** — Lecciones aprendidas y próximos pasos.

## ¿Para quién es?

Para estudiantes, practicantes de ML y cualquier persona que quiera ver cómo se
conectan todas las piezas de un proyecto de machine learning *más allá del notebook*.

## Dataset

Se usa el archivo [`heart.csv`](https://www.kaggle.com/datasets/fedesoriano/heart-failure-prediction),
con **918 registros** y **11 variables clínicas** (edad, sexo, tipo de dolor de
pecho, presión, colesterol, ECG, frecuencia cardíaca máxima, etc.).  La variable
objetivo `HeartDisease` es binaria: `0` = sin enfermedad, `1` = con enfermedad.

## Stack tecnológico

| Etapa | Herramientas |
|---|---|
| Análisis y modelado | Python, pandas, scikit-learn, matplotlib |
| Servicio / API | FastAPI, Pydantic, uvicorn |
| Empaquetado | Docker |
| Orquestación | Kubernetes (local) |
| Testing | pytest, FastAPI TestClient |
| CI/CD | GitHub Actions |
| Monitoreo | Evidently |

```{admonition} Cómo leer este libro
:class: note

Cada capítulo es autocontenido. Si ya conoces una parte (por ejemplo, sabes cómo
funciona un `Pipeline` de scikit-learn) puedes saltar directamente al capítulo que
más te interese. Los notebooks están ejecutados: verás las salidas reales del
código sin necesidad de correrlo localmente.
```
