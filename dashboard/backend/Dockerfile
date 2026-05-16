FROM python:3.11-slim

WORKDIR /app

# Accept build argument for requirements file (defaults to lightweight for easy start)
ARG REQUIREMENTS_FILE=requirements-light.txt

# Copy only the requirements file first for layer caching
COPY ${REQUIREMENTS_FILE} ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Ensure project root is in path (handled by main.py but good to have)
ENV PYTHONPATH=/app

CMD ["python", "-m", "dashboard.backend.main"]
