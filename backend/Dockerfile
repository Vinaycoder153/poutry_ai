FROM python:3.10-slim

# Install build dependencies for psycopg2 and healthcheck tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY backend/app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend app code
COPY backend/app/ ./app/

# Copy ml_pipeline code for retraining
COPY ml_pipeline/ ./ml_pipeline/

# Copy baseline dataset images
COPY poutry_ai/dataset/ ./poutry_ai/dataset/

# Create uploads and checkpoints folders in working directory
RUN mkdir -p /app/backend/uploads /app/ml_pipeline/checkpoints/final

# Expose FastAPI port
EXPOSE 8000

# Health check setup
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Start the uvicorn application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
