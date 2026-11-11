#!/bin/bash
set -e

echo "=================================================="
echo "Starting Zoe Enterprise SaaS Services on Railway"
echo "=================================================="

# 1. Start Multi-Bot Telegram Orchestrator in background
echo "Launching Multi-Bot Telegram Orchestrator..."
python -u scripts/run_all_bots.py --projects live_test onelove &
ORCH_PID=$!
echo "Orchestrator running with PID: $ORCH_PID"

# 2. Start FastAPI Server in foreground
echo "Launching FastAPI REST API on port ${PORT:-8000}..."
cd saas-dashboard/backend
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

