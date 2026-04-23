# 3.3 Cierre · del modelo a un artefacto desplegable

El notebook dejó varias cosas resueltas:

## Resultados de la comparación

| Modelo | CV AUC | Test AUC | Test Accuracy |
|---|---|---|---|
| **KNN** | 0.9141 | **0.9534** | **0.9239** |
| SVC | 0.9245 | 0.9497 | 0.8913 |
| Random Forest | 0.9288 | 0.9362 | 0.8967 |
| Logistic Regression | 0.9226 | 0.9323 | 0.8913 |

El ganador por Test AUC es **KNN** con `n_neighbors=9` y `weights='distance'`.

## Matriz de confusión del modelo final

```
           Pred 0   Pred 1
Real 0       75        7
Real 1        7       95
```

- **Verdaderos negativos**: 75
- **Verdaderos positivos**: 95
- **Falsos negativos** (dijo sano, estaba enfermo): 7 — es el error **clínicamente
  más grave**.
- **Falsos positivos** (dijo enfermo, estaba sano): 7

## Lo que se exportó

El archivo `model.joblib` no es sólo el modelo KNN, es el **Pipeline completo**:

```
preprocessor (ColumnTransformer)
├── num → imputer(median) → StandardScaler
└── cat → imputer(most_frequent) → OneHotEncoder
        │
        ▼
    KNeighborsClassifier(n_neighbors=9, weights='distance')
```

Esto es crítico: cuando la API reciba un JSON crudo como

```json
{ "Age": 58, "Sex": "M", "ChestPainType": "ASY", ... }
```

el pipeline cargado sabrá **automáticamente** escalar los números y codificar
las categorías antes de pasarle el vector final al KNN.  La API no necesita
conocer ningún detalle del preprocesamiento.

```{admonition} Próximo paso
:class: tip

En el capítulo 4 tomamos este `model.joblib` y lo convertimos en un servicio
HTTP con FastAPI, listo para recibir predicciones en producción.
```
