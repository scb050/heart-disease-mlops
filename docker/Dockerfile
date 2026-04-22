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

# Copiar codigo y modelo
COPY app /app/app
COPY model.joblib /app/model.joblib

EXPOSE 8000

# Healthcheck para Kubernetes y docker run
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/').read()" || exit 1

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
