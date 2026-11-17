# Zoe AI Intelligence Engine & Web3 Community SaaS

[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2015-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Solana](https://img.shields.io/badge/Chain-Solana%20%7C%20EVM-9945FF.svg)](https://solana.com/)
[![TailwindCSS](https://img.shields.io/badge/UI-WealthWave%20Dark-00ff66.svg)](https://tailwindcss.com/)

Zoe is an enterprise-grade AI-powered Web3 Community Management, Multi-Chain Token Intelligence Scanner, Paper Trading, and Autonomous Moderation platform. Designed with the high-performance **WealthWave Dark UI** (`#0a0a0a` background with `#00ff66` neon accents), Zoe empowers crypto founders, trading communities, and retail investors with autonomous protection, deep intelligence, and risk analysis.

---

## Architecture Overview

```
                      ┌───────────────────────────────────────────────┐
                      │             ZOE PLATFORM ARCHITECTURE          │
                      └───────────────────────────────────────────────┘
                                              │
              ┌───────────────────────────────┴───────────────────────────────┐
              ▼                                                               ▼
   ┌───────────────────────┐                                       ┌───────────────────────┐
   │    ZOE CORE ENGINE    │                                       │   SAAS WEB DASHBOARD  │
   │ (Autonomous Sub-Bots) │                                       │  (FastAPI + Next.js)  │
   └──────────┬────────────┘                                       └──────────┬────────────┘
              │                                                               │
     ┌────────┴────────┐                                            ┌─────────┴─────────┐
     ▼                 ▼                                            ▼                   ▼
┌───────────┐   ┌───────────┐                              ┌─────────────────┐   ┌─────────────────┐
│ Telegram  │   │ Telegram  │                              │ Multi-Chain     │   │ Paper Trading   │
│ One Love  │   │Hummingbird│                              │ Scanner Engine  │   │ Terminal        │
│ Bot       │   │ Bot       │                              └────────┬────────┘   └────────┬────────┘
└─────┬─────┘   └─────┬─────┘                                       │                     │
      │               │                                             ▼                     ▼
      └───────┬───────┘                                    ┌─────────────────┐   ┌─────────────────┐
              ▼                                            │ Deep Wallet &   │   │ On-Chain Solana │
    Autonomous Moderation:                                 │ Token Tracing   │   │ USDT Gateway    │
    - Anti-Spam & Phishing                                 └─────────────────┘   └─────────────────┘
    - Instant Mute & Ban
    - Real-Time Conversation Logs
```

---

## Key Modules & Features

### 1. Autonomous Telegram Sub-Bots & Moderation (Mega-Modules 1–5, 8)
- **Active Community Moderation:** Automatically inspects incoming messages in Telegram groups for malicious scam links, phishing domains, and flood attacks.
- **Enforcement Actions:** Automatically mutes or bans violators, deletes scam messages in real-time, and announces policy actions to the chat.
- **RAG-Powered Knowledge Base:** Instant semantic retrieval over whitepapers, tokenomics, and roadmap documents to answer user inquiries accurately.
- **Multi-Bot Management:** Supports distinct sub-bots simultaneously (e.g. *One Love Bot*, *Hummingbird Bot*, *Custom Projects*).

### 2. Universal Multi-Chain Intelligence Scanner & AI Analyst (Mega-Modules 7 & Universal Multi-Chain)
- **Cross-Chain Support:** Solana (`base58` addresses) and EVM (`0x` addresses for Ethereum, Base, Binance Smart Chain, Arbitrum, and Polygon).
- **Deep Wallet Tracing:** Analyzes the creator/dev wallet to detect initial funding sources (e.g. centralized exchanges vs. mixer/scam wallets) and remaining dev holdings.
- **Audit & Safety Scoring:** Calculates an aggregated 0–100 Safety Score factoring in liquidity lock status, mint authority, freeze authority, top 10 holder concentration, and honeypot indicators.
- **AI Analyst Verdict:** Synthesizes on-chain signals into an actionable institutional risk evaluation (LOW, MEDIUM, HIGH, CRITICAL).

### 3. Paper Trading Engine (Mega-Module 11)
- **Virtual Capital:** Every user gets a simulated balance of **$10,000 USDT** to test trading strategies without risking capital.
- **Live Price Feeds:** Orders executed against live DexScreener spot prices.
- **Full Portfolio Accounting:** Tracks open positions, average entry prices, real-time unrealized and realized P&L, and trade histories.

### 4. Non-Custodial SaaS Payment Gateway & Entitlements (Mega-Module 6)
- **On-Chain Solana USDT Verification:** Direct peer-to-peer verification via public Solana RPC without third-party fees (Stripe/intermediaries).
- **Instant Entitlement Unlocking:** Validated blockchain transaction signatures immediately upgrade accounts to the Premium tier.

### 5. Super Admin Master Control & Owner Analytics (Mega-Modules 9, 10, 12)
- **Super Admin Dashboard:** Platform-wide oversight displaying Monthly Recurring Revenue (MRR), total active client projects, live bot statuses, and instant client suspension/activation controls.
- **Project Owner Analytics:** Conversation volume, message sentiment distribution, top community questions, and live conversation log streaming.
- **Notification Center & User Settings:** Real-time bell notification dropdown for liquidity drops and account alerts, plus user profile, password management, and billing invoice history.

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, Lucide Icons |
| **Backend API** | FastAPI, Pydantic v2, Uvicorn, Python 3.12 |
| **Database & Auth** | Supabase (PostgreSQL + RLS) with SQLite automatic zero-config local fallback; PyJWT, Passlib (Bcrypt) |
| **Blockchain** | Solana JSON-RPC Client, Web3.py / EVM RPCs, DexScreener REST API |
| **AI / LLM** | Google Gemini 2.0 / 1.5, FAISS Vector Store, Sentence-Transformers |
| **Styling** | WealthWave Dark Theme (`#0a0a0a` background, `#121212` cards, `#00ff66` neon green accents) |

---

## Quick Start & Local Development

### Prerequisites
- Python 3.12+
- Node.js 18+ and `npm`
- Git

### 1. Backend Setup

```powershell
# 1. Clone repository
git clone https://github.com/Zoestrings/zoe-saas.git
cd zoe

# 2. Create and activate virtual environment
py -3.12 -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r saas-dashboard/backend/requirements.txt

# 4. Configure environment
copy saas-dashboard\backend\.env.example saas-dashboard\backend\.env

# 5. Start the FastAPI backend
$env:PYTHONPATH="src;saas-dashboard/backend"
uvicorn saas-dashboard.backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup

```powershell
# 1. Navigate to frontend directory
cd saas-dashboard/frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) to open the WealthWave dashboard.

---

## Demo Seeding & Verification

Zoe includes automated scripts for demo data preparation and full end-to-end regression testing.

### Populate Realistic Demo Data
Populates the dashboard with 3 realistic projects (*Pepe Coin Community*, *RocketX Network*, *MoonCat DAO*), 5 multi-chain token security investigations, 3 paper trades, and billing invoices:

```powershell
$env:PYTHONPATH="src;saas-dashboard/backend"
.venv\Scripts\python.exe saas-dashboard/backend/seed_demo.py
```

### Run End-to-End System Verification
Executes an automated 5-step test verifying registration, project management, token investigation, paper trading execution, and billing history:

```powershell
$env:PYTHONPATH="src;saas-dashboard/backend"
.venv\Scripts\python.exe saas-dashboard/backend/test_e2e.py
```

### Run Backend Unit & Integration Tests
```powershell
$env:PYTHONPATH="src;saas-dashboard/backend"
.venv\Scripts\python.exe -m pytest saas-dashboard/backend/tests
```

### Build Frontend for Production
```powershell
cd saas-dashboard/frontend
npm run build
```

---

## Directory Structure

```
zoe/
├── config/                          # Bot configuration & project settings
├── saas-dashboard/
│   ├── backend/                     # FastAPI backend
│   │   ├── main.py                  # API endpoints (Auth, Scanner, Trading, Admin)
│   │   ├── database.py              # Supabase & SQLite hybrid persistence
│   │   ├── seed_demo.py             # Realistic sales demo data seeder
│   │   ├── test_e2e.py              # End-to-end full platform verification
│   │   └── tests/                   # Pytest test suite (30+ test cases)
│   └── frontend/                    # Next.js 15 React application
│       ├── src/
│       │   ├── app/
│       │   │   ├── page.tsx         # Public marketing landing page
│       │   │   ├── login/           # User authentication
│       │   │   ├── register/        # Registration & role initialization
│       │   │   ├── investigate/     # Multi-chain token scanner & AI analyst
│       │   │   ├── trading/         # $10k Paper Trading terminal
│       │   │   ├── watchlist/       # Token monitoring & real-time alerts
│       │   │   ├── settings/        # Profile, security & invoice history
│       │   │   ├── admin/           # Super Admin master control & revenue
│       │   │   └── projects/        # Project owner command center & logs
│       │   └── components/          # WealthWave UI components (header, sidebar)
└── src/zoe/                         # Core Python AI Engine & Telegram Sub-Bots
    ├── core/                        # Engine orchestration & config
    ├── tools/                       # Multi-chain scanners, DexScreener, Solana RPC
    └── storage/                     # Vector stores & SQLite state
```

---

## License
MIT License. Copyright (c) 2026 Zoe Intelligence.
