# Production Dockerfile optimized for Railway cloud containers
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app:/app/src"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU first to prevent RAM exhaustion and build timeout
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install AI & Core Engine dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Backend dependencies
COPY saas-dashboard/backend/requirements.txt saas-backend-requirements.txt
RUN pip install --no-cache-dir -r saas-backend-requirements.txt

# Create runtime directories needed by the SQLite databases and FAISS indexes
RUN mkdir -p /app/data/operational /app/data/official_knowledge /app/data/community_memory /app/data/indexes /app/data/tmp /app/config/secrets

# Copy codebase and approval docs needed for live send verification
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY docs/ ./docs/
COPY saas-dashboard/backend/ ./saas-dashboard/backend/

EXPOSE 8000

CMD ["sh", "-c", "python -u scripts/run_all_bots.py --projects live_test onelove & cd saas-dashboard/backend && exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
