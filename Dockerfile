# Production Dockerfile for Zoe Backend & Multi-Tenant Bot Orchestrator
FROM python:3.11-slim

# Prevent Python from writing .pyc and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app:/app/src"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install root dependencies (Core AI, FAISS, PyTorch, Telegram Adapter, Bot Orchestrator)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install backend dependencies (FastAPI, Supabase, Cryptography)
COPY saas-dashboard/backend/requirements.txt saas-backend-requirements.txt
RUN pip install --no-cache-dir -r saas-backend-requirements.txt

# Copy project code and configs
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY data/ ./data/
COPY saas-dashboard/backend/ ./saas-dashboard/backend/

# Expose FastAPI port
EXPOSE 8000

# Start script running both FastAPI backend and Multi-Bot Telegram Orchestrator
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]

