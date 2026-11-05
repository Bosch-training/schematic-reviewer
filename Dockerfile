FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Placeholder until api.main exposes a FastAPI `app`; then use uvicorn api.main:app.
CMD ["python", "-m", "http.server", "8000"]
