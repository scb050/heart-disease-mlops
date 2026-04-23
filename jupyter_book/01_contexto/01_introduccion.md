# 1.1 Introducción y objetivos

## El problema

La enfermedad cardiovascular sigue siendo la **principal causa de muerte en el
mundo**. Detectar a tiempo a los pacientes con mayor riesgo es una tarea clínica
compleja que se apoya tanto en el criterio del médico como en variables
cuantitativas medibles (presión, colesterol, ECG, frecuencia cardíaca, etc.).

El objetivo de este proyecto **no es reemplazar al médico**, sino construir un
**modelo estadístico de apoyo** que a partir de esas variables entregue una
probabilidad de enfermedad y lo haga disponible como un servicio web reutilizable.

## Objetivos concretos

El proyecto cumple con los siguientes objetivos específicos:

1. Demostrar, de forma intencional, qué es una **fuga de datos** (*data leakage*) y
   por qué produce métricas engañosamente buenas.
2. Construir un **pipeline seguro** de preprocesamiento + modelo usando
   `Pipeline` y `GridSearchCV` de scikit-learn.
3. Comparar varios algoritmos (Logistic Regression, KNN, Random Forest, SVC) con
   validación cruzada estratificada y seleccionar el mejor por AUC.
4. Exportar el mejor modelo como `model.joblib` y exponerlo mediante una **API
   REST** con FastAPI.
5. **Empaquetar** la API en una imagen Docker y desplegarla en un clúster
   Kubernetes local.
6. Agregar **tests automáticos** con pytest y un pipeline de integración continua.
7. Implementar **monitoreo de drift** con Evidently sobre los datos de entrada.

## ¿Por qué MLOps?

Un modelo que solo vive en un notebook **no es útil en producción**.  MLOps es
el conjunto de prácticas que permiten:

- Reproducibilidad del entrenamiento.
- Despliegue automatizado del modelo.
- Observabilidad (logs, métricas, drift).
- Tests que verifican que la API sigue funcionando después de cada cambio.

Este libro recorre exactamente esa transición: del notebook al servicio operado.

```{admonition} Mapa del recorrido
:class: tip

- **Capítulo 2** → el problema de la fuga de datos.
- **Capítulo 3** → cómo resolverlo con un pipeline robusto.
- **Capítulo 4** → cómo servir el modelo a otros.
- **Capítulo 5** → cómo saber si el modelo sigue funcionando bien mañana.
```
