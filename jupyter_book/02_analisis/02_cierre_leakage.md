# 2.3 Cierre · lecciones del capítulo

El notebook anterior mostró, con números, el efecto de la fuga:

| Escenario | AUC |
|---|---|
| Con fuga (variable derivada de `y` + escalado global) | **1.0000** |
| Sin fuga (split primero, `fit_transform` solo en train) | **0.8881** |

Una diferencia de **0.11 puntos de AUC** que parecía una mejora milagrosa, pero
era pura contaminación.

## Qué rescatar para el resto del proyecto

```{admonition} Regla 1 · El split va primero
:class: important

Antes de mirar estadísticas, escalar, imputar o codificar, **hacé el
`train_test_split` (o la validación cruzada)**.  Todo lo demás se hace sobre el
conjunto adecuado.
```

```{admonition} Regla 2 · Preprocesamiento dentro del Pipeline
:class: important

Si el preprocesamiento está ENCAPSULADO dentro de un `Pipeline` de sklearn y el
`Pipeline` se pasa a `GridSearchCV`, la fuga se vuelve prácticamente imposible
porque cada fold re-ajusta el preprocesamiento con sus propios datos.
```

```{admonition} Regla 3 · Atención a las variables "mágicas"
:class: important

Si una feature te da un AUC sospechosamente alto, duda.  Preguntate: *¿en
producción esta variable va a estar disponible al momento de predecir?*  Si la
respuesta es "no" o "a veces", es fuga.
```

## Dónde vamos ahora

En el capítulo siguiente construimos el pipeline real y seguro:

- Manejamos variables numéricas **y** categóricas.
- Comparamos 4 modelos con `GridSearchCV`.
- Seleccionamos al ganador por AUC en test.
- Exportamos el pipeline completo a `model.joblib` para desplegarlo.
