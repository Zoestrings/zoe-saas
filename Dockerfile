# Production Dockerfile for Zoe Backend & Multi-Tenant Bot Orchestrator
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app:/app/src"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY saas-dashboard/backend/requirements.txt saas-backend-requirements.txt
RUN pip install --no-cache-dir -r saas-backend-requirements.txt

COPY src/ ./src/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY data/ ./data/
COPY saas-dashboard/backend/ ./saas-dashboard/backend/

EXPOSE 8000

CMD ["sh", "-c", "python -u scripts/run_all_bots.py --projects live_test onelove & cd saas-dashboard/backend && exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
