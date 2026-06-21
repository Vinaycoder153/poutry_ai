# Stage 1: Build the React frontend
FROM node:20-alpine AS builder
WORKDIR /app/frontend

COPY poutry_ai/package*.json ./
RUN npm install

COPY poutry_ai/ ./
RUN npm run build

# Stage 2: Build the FastAPI backend and assemble the app
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY backend/app/requirements.txt ./backend/app/
RUN pip install --no-cache-dir -r backend/app/requirements.txt

# Copy Python backend code
COPY backend/app/ ./backend/app/

# Copy ML pipeline scripts and checkpoints
COPY ml_pipeline/ ./ml_pipeline/

# Copy baseline dataset images
COPY poutry_ai/dataset/ ./poutry_ai/dataset/

# Copy compiled React frontend static build
COPY --from=builder /app/frontend/dist ./poutry_ai/dist

# Create necessary directories
RUN mkdir -p /app/backend/uploads /app/ml_pipeline/checkpoints/final

# Adjust permissions for Hugging Face Spaces (user 1000)
RUN chown -R 1000:1000 /app && chmod -R 777 /app

# Expose Hugging Face default port
EXPOSE 7860

# Define env variables
ENV PORT=7860
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend

# Run as non-root user 1000
USER 1000

# Start the uvicorn application
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}"]
