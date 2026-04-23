# 2.1 ¿Qué es la fuga de datos?

Antes de entrar al notebook, vale la pena dejar claras las ideas que vamos a
demostrar.

## Definición

Una **fuga de datos** (*data leakage*) ocurre cuando, durante el entrenamiento,
el modelo accede a información que **no estará disponible en el momento de la
predicción real**.  El resultado es un modelo que aprende a "hacer trampa":
obtiene métricas excelentes en el notebook y fracasa en producción.

## Dos formas típicas de fuga

```{admonition} 1 · Fuga por variables
:class: warning

Incluir en `X` una columna que de algún modo **contiene** la información de `y`.
Por ejemplo: usar el resultado de un examen que sólo se hace DESPUÉS del
diagnóstico.
```

```{admonition} 2 · Fuga por preprocesamiento
:class: warning

Ajustar transformaciones (imputación, escalado, encoding) usando el dataset
COMPLETO antes de hacer el `train_test_split`.  El conjunto de prueba contamina
las estadísticas del preprocesador.
```

## ¿Por qué la fuga es tan peligrosa?

- **Las métricas mienten**: el AUC en CV puede ser 0.99 y la realidad ser 0.75.
- **Es difícil de detectar**: no hay error, todo "funciona".
- **Se descubre en producción**: cuando el daño (clínico, comercial, legal) ya
  está hecho.

## Qué vamos a hacer en este notebook

1. Armar dos escenarios con los **mismos datos** y el **mismo modelo** (SVC).
2. En el primero introducimos de forma intencional una variable `leaky_feature`
   derivada de `y`, y escalamos todo el dataset antes del split.
3. En el segundo hacemos el split primero y escalamos únicamente con el
   entrenamiento.
4. Comparamos el AUC de ambos.

El objetivo no es obtener el mejor modelo — eso lo haremos en el capítulo
siguiente — sino **ver con los ojos** por qué la fuga hace daño.

```{admonition} Ojo con el orden
:class: tip

La regla de oro es simple: **el conjunto de prueba no debe influir en ninguna
decisión que se tome durante el entrenamiento**.  Ni selección de variables, ni
ajuste de hiperparámetros, ni estadísticas de escalado.
```
