#!/bin/bash
set -e

echo "=================================================="
echo "Starting Zoe Enterprise SaaS Services on Railway"
echo "=================================================="

# Dispatch based on SERVICE_ROLE to prevent dual-polling conflicts
if [ "$SERVICE_ROLE" = "worker" ]; then
    echo "Launching Multi-Bot Telegram Orchestrator (Worker Role)..."
    exec python -u scripts/run_all_bots.py
else
    echo "Launching FastAPI REST API (Backend Role) on port ${PORT:-8000}..."
    cd saas-dashboard/backend
    exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
fi

