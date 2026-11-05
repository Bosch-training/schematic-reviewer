FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Serves the static page; switch to uvicorn api.main:app once api.main exposes a FastAPI `app`.
CMD ["python", "-m", "http.server", "8000", "--directory", "frontend/web"]
