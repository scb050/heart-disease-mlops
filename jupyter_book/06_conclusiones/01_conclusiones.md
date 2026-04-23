# 6.1 Conclusiones y próximos pasos

## Lo que se logró

Este proyecto atraviesa las **siete etapas** típicas de un ciclo de MLOps:

| Etapa | Entregable | Estado |
|---|---|---|
| Análisis de datos | Notebook 1 · demostración de fuga | ✅ |
| Entrenamiento seguro | Notebook 2 · Pipeline + GridSearchCV | ✅ |
| Artefacto de modelo | `model.joblib` | ✅ |
| Servicio HTTP | FastAPI con validación Pydantic | ✅ |
| Empaquetado | Docker + requirements fijos | ✅ |
| Orquestación | Manifiestos Kubernetes (Deployment + Service) | ✅ |
| Calidad | pytest + GitHub Actions | ✅ |
| Observabilidad | Reporte de drift con Evidently | ✅ |

El **modelo final** es un pipeline KNN con `n_neighbors=9` y `weights='distance'`
que obtiene **AUC = 0.95** en test, con una matriz de confusión equilibrada
(7 falsos positivos, 7 falsos negativos de 184 casos).

## Lecciones claves del proyecto

### 1 · La fuga de datos es silenciosa pero grave

Una diferencia de **0.11 puntos de AUC** entre el flujo con fuga y el flujo
limpio basta para que un modelo parezca "listo" sin estarlo.  La herramienta
más efectiva para evitarlo es **encapsular el preprocesamiento dentro del
`Pipeline`** y dejar que `GridSearchCV` haga el trabajo correcto en cada fold.

### 2 · El Pipeline es el contrato de producción

Exportar el **pipeline completo** (preprocesamiento + modelo) hace que la API
sea **tonta a propósito**: sólo recibe JSON, lo pasa a un DataFrame y llama a
`predict`.  Toda la lógica de transformación viaja dentro de `model.joblib`.

### 3 · Pydantic es tu primera línea de defensa

Los `Field(ge=..., le=...)` y los `Literal[...]` atrapan datos malos **antes** de
que lleguen al modelo.  Esto previene predicciones raras y además documenta el
contrato en `/docs`.

### 4 · Docker impone reproducibilidad

La combinación **versiones pinneadas + imagen inmutable** significa que lo que
pasó en el notebook pasa también en producción.  Sin sorpresas de versión.

### 5 · Los tests más valiosos son los semánticos

El test `test_high_risk_has_higher_probability_than_low_risk` no verifica un
número, verifica un **comportamiento**.  Sobrevive a reentrenamientos, cambios
de algoritmo y reajustes de hiperparámetros.

### 6 · El drift no es un bug, es una señal

Un reporte de drift que dispara alarma **no significa que el modelo falla** —
significa que el mundo cambió.  La decisión de reentrenar es **humana**, no
automática.

## Qué quedaría para una versión 2.0

```{admonition} Mejoras técnicas
:class: note

- **Registro de experimentos** con MLflow o Weights & Biases.
- **Model registry** con versionado formal de modelos.
- **Feature store** si el dominio crece y varias APIs comparten features.
- **A/B testing** entre versiones de modelo en producción.
- **Reentrenamiento automático** disparado por drift.
- **Observabilidad avanzada** con Prometheus + Grafana para latencia, errores
  y distribución de predicciones.
```

```{admonition} Mejoras de producto
:class: note

- **Explicabilidad por paciente** con SHAP para cada predicción.
- **Calibración de probabilidades** con `CalibratedClassifierCV`.
- **Intervalos de confianza** o estimación de incertidumbre.
- **Multi-modelo** para distintas poblaciones (edad, comorbilidades).
- **Autenticación** y audit log para uso clínico real.
```

## Reflexión final

La diferencia entre un proyecto de machine learning **de laboratorio** y un
proyecto **de MLOps** no está en el algoritmo.  Está en las preguntas que se
hacen alrededor del algoritmo:

- ¿Cómo sé que los datos son válidos?
- ¿Cómo sé que el modelo se entrenó correctamente?
- ¿Cómo sé que la API no está rota?
- ¿Cómo sé que sigue funcionando bien dentro de dos meses?

Este libro es la versión operable de esas preguntas: cada capítulo resuelve
una, y todos juntos forman un sistema que pasa del notebook al mundo real.

```{admonition} Gracias
:class: tip
Si llegaste hasta acá, gracias por recorrer el proyecto completo.  Espero que
la experiencia haya sido más útil que intentar descifrar un `main.py` de
mil líneas.
```
