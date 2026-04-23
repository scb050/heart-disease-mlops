# 4.2 Contenerización con Docker

Una API que "funciona en mi máquina" no es una API desplegable.  Docker la
convierte en una **unidad inmutable y portable**: misma imagen en desarrollo,
tests, CI y producción.

## El Dockerfile

El archivo [`docker/Dockerfile`](../../docker/Dockerfile) es muy compacto:

```dockerfile
FROM python:3.10-slim

# Evita prompts y logs bufferizados
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Instalar dependencias primero (mejor cacheo)
COPY docker/requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar código y modelo
COPY app /app/app
COPY model.joblib /app/model.joblib

EXPOSE 8000

# Healthcheck para Kubernetes y docker run
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/').read()" || exit 1

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Decisiones de diseño explicadas

### 1 · Imagen base `python:3.10-slim`

- **`slim`** porque no necesitamos todo el ecosistema Debian. Ahorra ~700 MB.
- **3.10** por compatibilidad estable con las versiones de scikit-learn /
  pandas / FastAPI que fijamos.

### 2 · Variables de entorno de Python

| Variable | Qué hace |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1` | No genera archivos `.pyc` — imagen más limpia. |
| `PYTHONUNBUFFERED=1` | `stdout`/`stderr` no se bufferizan → los logs llegan en tiempo real a Kubernetes / `docker logs`. |
| `PIP_NO_CACHE_DIR=1` | pip no guarda el cache de descargas → imagen más chica. |

### 3 · Copiar `requirements.txt` antes que el código

Docker cachea por capa.  Si separamos la instalación de dependencias de la
copia del código, un cambio en `app/api.py` **no obliga a reinstalar nada**.  El
build cae de minutos a segundos durante el desarrollo.

### 4 · Copiar `model.joblib` dentro de la imagen

El modelo viaja **dentro de la imagen**.  Alternativa: montarlo como volumen.

- **Dentro de la imagen** → reproducibilidad total. Si el modelo cambia, hay
  una imagen nueva con tag nuevo. Ideal para CI/CD.
- **Volumen** → permite actualizar el modelo sin redeploy, pero rompe la
  inmutabilidad y complica el rollback.

En este proyecto elegimos **dentro de la imagen** porque el modelo es pequeño
(unos pocos MB) y el versionado por tag es más limpio.

### 5 · Healthcheck integrado

El `HEALTHCHECK` le da a Docker/Kubernetes una forma de saber si el contenedor
está vivo.  Hace una petición HTTP interna a `/` cada 30 segundos.  Si falla 3
veces seguidas, el contenedor se marca como *unhealthy* y Kubernetes lo reinicia.

### 6 · `CMD` con Uvicorn

El entrypoint final es Uvicorn sirviendo `app.api:app` en el puerto 8000.

```{admonition} Para producción
:class: note

En producción conviene correr uvicorn **detrás de gunicorn** con varios
workers: `gunicorn -k uvicorn.workers.UvicornWorker app.api:app -w 4`.
En este proyecto mantenemos uvicorn directo para simplicidad didáctica.
```

## Las dependencias

El archivo [`docker/requirements.txt`](../../docker/requirements.txt) fija
versiones exactas:

```
fastapi==0.115.0
uvicorn==0.30.6
scikit-learn==1.7.2
pandas==2.2.3
numpy==2.1.1
joblib==1.4.2
pydantic==2.9.2
```

```{admonition} Importante
:class: warning

La versión de **scikit-learn** en el Dockerfile **debe coincidir** con la que
se usó para entrenar el modelo.  Si se reentrena con una versión distinta,
actualiza aquí también, o el `joblib.load` puede fallar con warnings o errores
de compatibilidad.
```

## Cómo construir y correr localmente

```bash
# Desde la raíz del proyecto
docker build -f docker/Dockerfile -t heart-api:latest .

# Correr el contenedor
docker run -p 8000:8000 heart-api:latest

# Test rápido
curl http://localhost:8000/health
```

## Tamaño y rendimiento esperados

| Métrica | Valor aproximado |
|---|---|
| Tamaño final de la imagen | ~400 MB |
| Tiempo de arranque (hasta responder `/health`) | < 3 s |
| Latencia de `/predict` en una CPU decente | 5–15 ms |
| Memoria en reposo | ~150 MB |
