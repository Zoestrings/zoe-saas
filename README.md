# Zoe Intelligence Engine — Stage 1

## Overview
Stage 1 sets up the initial repository skeleton, database connection helpers, operational schema, configuration loader, and hardware verification harness.

Stage 1 explicitly does **not**:
- Connect to Telegram or poll for updates.
- Call any LLM provider (mock or real).
- Install `torch`, `faiss-cpu`, or `sentence-transformers` into the application environment (`.venv/`).
- Implement RAG, memory, or participation logic.

---

## Environment Setup

Because Windows App Execution Aliases may intercept `python`/`python3`, always create virtual environments using the Windows Python launcher `py`:

### 1. Application Virtual Environment (`.venv/`)
```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Isolated Hardware Spike Environment (`.venv-spike/`)
The spike environment is strictly isolated from the application environment:
```powershell
py -3.12 -m venv .venv-spike
.venv-spike\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install faiss-cpu sentence-transformers psutil
```

---

## Running the Hardware Spike
From within `.venv-spike/`:
```powershell
.venv-spike\Scripts\activate
python -m zoe.utils.spike
```
Fill in the measured values and notes into `docs/HARDWARE_SPIKE.md`.

---

## Running Tests
From within `.venv/`:
```powershell
.venv\Scripts\activate
pytest
```

---

## Secrets Configuration
Secrets must never be committed. Provide secrets in `config/secrets/{project_id}.secrets.yaml`:

```yaml
telegram:
  bot_token: "YOUR_TELEGRAM_BOT_TOKEN"

llm:
  provider_api_key: "YOUR_API_KEY"

security:
  hmac_key: "YOUR_HMAC_KEY"
```

$env:PYTHONPATH="src;scripts"; $env:PYTHONUNBUFFERED="1"; .venv\Scripts\python.exe -u scripts/run_all_bots.py --projects onelove live_test