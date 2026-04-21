FROM python:3.10-slim

WORKDIR /app

COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app
COPY model.joblib /app/model.joblib

EXPOSE 8000

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
