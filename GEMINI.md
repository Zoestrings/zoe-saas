# Antigravity Workspace Rules

## Automated Web Scraping & Ingestion
- When I paste a URL and say "Scrape this", you must run the command:
  ```powershell
  $env:PYTHONPATH='src'; .venv\Scripts\python.exe scripts/scrape_and_ingest.py <URL>
  ```
- Do not write new code for scraping unless the script fails.

