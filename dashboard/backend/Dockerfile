FROM python:3.11-slim

WORKDIR /app

# Copy and install requirements from project root
COPY ../../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY ../.. .

WORKDIR /app

CMD ["uvicorn", "dashboard.backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
