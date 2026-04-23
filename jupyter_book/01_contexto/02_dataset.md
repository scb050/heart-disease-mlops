# 1.2 El dataset `heart.csv`

El dataset contiene **918 registros** de pacientes y **11 variables predictoras**
más la variable objetivo `HeartDisease`.  Es un dataset tabular clásico y bien
curado, lo que permite concentrarnos en el flujo MLOps sin gastar energía en
limpieza de datos.

## Variables

| Variable | Tipo | Descripción | Valores |
|---|---|---|---|
| `Age` | numérica | Edad del paciente en años | entero, típicamente 28–77 |
| `Sex` | categórica | Sexo biológico | `M`, `F` |
| `ChestPainType` | categórica | Tipo de dolor de pecho | `ATA`, `NAP`, `ASY`, `TA` |
| `RestingBP` | numérica | Presión arterial en reposo (mmHg) | entero |
| `Cholesterol` | numérica | Colesterol sérico (mg/dl) | entero |
| `FastingBS` | categórica binaria | Glucemia en ayunas > 120 mg/dl | `0`, `1` |
| `RestingECG` | categórica | Resultado del ECG en reposo | `Normal`, `ST`, `LVH` |
| `MaxHR` | numérica | Frecuencia cardíaca máxima alcanzada | entero |
| `ExerciseAngina` | categórica | Angina inducida por ejercicio | `Y`, `N` |
| `Oldpeak` | numérica | Depresión ST inducida por ejercicio | decimal |
| `ST_Slope` | categórica | Pendiente del segmento ST | `Up`, `Flat`, `Down` |
| **`HeartDisease`** | **objetivo** | **Presencia de enfermedad** | **`0`, `1`** |

## Diccionario clínico rápido

- **Dolor de pecho** — `ASY` (asintomático) es, paradójicamente, el más asociado
  con enfermedad en este dataset.
- **ECG en reposo** — `ST` y `LVH` indican anomalías eléctricas/hipertrofia.
- **Angina por ejercicio** — `Y` se asocia fuertemente con el diagnóstico positivo.
- **Oldpeak** — valores más altos de depresión ST son señal de isquemia.
- **ST_Slope** — `Flat` y `Down` son más preocupantes que `Up`.

## Distribución de la variable objetivo

```
HeartDisease
1    508   (55.3 %)
0    410   (44.7 %)
```

El dataset está **moderadamente balanceado**. No es necesario aplicar técnicas de
*oversampling* o *class weights*, pero sí conviene usar `stratify=y` en el
`train_test_split` para mantener la proporción en ambos conjuntos.

## Calidad del dataset

- **Sin valores nulos** en ninguna columna.
- **Sin duplicados** relevantes.
- **Tamaño manejable** → no se requieren técnicas de big data.

```{admonition} Decisión de diseño
:class: note

A pesar de que el dataset no tiene nulos, en el pipeline vamos a incluir un
`SimpleImputer`.  Esto **no es redundante**: nos prepara para el escenario de
producción, donde la API puede recibir datos incompletos o corruptos y el
pipeline debe saber cómo manejarlos sin romperse.
```
