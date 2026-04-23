# 3.1 Pipelines, ColumnTransformer y validación cruzada

Este capítulo es el corazón de la parte de modelado.  Vamos a construir un flujo
robusto que:

- Previene la fuga de datos que vimos en el capítulo anterior.
- Trata correctamente variables **numéricas y categóricas**.
- Compara múltiples modelos con **validación cruzada estratificada**.
- Entrega un único artefacto `model.joblib` listo para ser servido por la API.

## Conceptos clave

### Pipeline

Un `Pipeline` de scikit-learn encadena pasos que se ejecutan en orden.  La gran
ventaja: **todo el flujo se comporta como un estimador**, así que puedes llamar
a `.fit()`, `.predict()` o `.predict_proba()` como si fuese un modelo normal.

```
Pipeline: [preprocesamiento]  →  [modelo]
```

### ColumnTransformer

Aplica **transformaciones distintas a columnas distintas** en un solo objeto.
En nuestro caso:

- A las columnas **numéricas** → imputación con mediana + `StandardScaler`.
- A las columnas **categóricas** → imputación con moda + `OneHotEncoder`.

### GridSearchCV

Busca la mejor combinación de hiperparámetros probando todas las variantes sobre
una **validación cruzada** (5 folds en nuestro caso).  Como recibe un `Pipeline`
completo, el preprocesamiento se reajusta correctamente en cada fold.

## Anatomía del flujo que vamos a construir

```
ColumnTransformer (preprocessor)
├── num → SimpleImputer(median) → StandardScaler
└── cat → SimpleImputer(most_frequent) → OneHotEncoder

        │
        ▼
Pipeline final = preprocessor → model (LogReg | KNN | RF | SVC)
        │
        ▼
GridSearchCV (cv=5, scoring='roc_auc')
        │
        ▼
Mejor estimador → evaluación en test → model.joblib
```

## Métrica elegida: AUC-ROC

Usamos **AUC-ROC** como métrica principal porque:

- Es **insensible al umbral** de decisión (0.5, 0.3, 0.7...).
- Funciona bien con clases **ligeramente desbalanceadas** (55/45 en este dataset).
- Permite comparar modelos que producen probabilidades muy diferentes.

```{admonition} Lectura intuitiva del AUC
:class: tip

El AUC es la probabilidad de que el modelo le asigne mayor score a un paciente
positivo que a uno negativo, elegidos al azar.  **AUC = 1** es perfecto, **AUC =
0.5** es adivinar a cara o cruz.
```

## Modelos que vamos a comparar

| Modelo | Fortalezas | Debilidades |
|---|---|---|
| Logistic Regression | Interpretable, rápido, estable | Lineal |
| KNN | No paramétrico, flexible | Sensible a escala y a dimensiones altas |
| Random Forest | No lineal, robusto, hace FS implícito | Caja negra, puede sobreajustar |
| SVC (RBF) | Buen desempeño en datasets medianos | Lento, sensible a hiperparámetros |

En la práctica: probamos los cuatro y que los números hablen.
