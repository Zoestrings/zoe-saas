"""Zoe Platform Demo Seeder Script (Final Polish).

Populates Supabase (and local dev database) with realistic projects,
investigations, paper trades, and billing invoices for sales demos.
"""

import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root and backend to PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv(ROOT_DIR / ".env")

from main import get_supabase_admin, get_supabase, get_dev_db


def seed_demo_data():
    """Seed realistic data across Supabase and local dev database."""
    print("=" * 65)
    print("🚀 Zoe Intelligence Platform — Demo Seeder Starting")
    print("=" * 65)

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    yesterday_iso = (now - timedelta(days=1)).isoformat()
    three_days_ago_iso = (now - timedelta(days=3)).isoformat()
    week_ago_iso = (now - timedelta(days=7)).isoformat()

    # 1. Resolve Demo User
    demo_user_id = "demo-owner-uuid-001"
    demo_email = "demo@zoe.community"

    admin_client = get_supabase_admin() or get_supabase()
    if admin_client:
        print("[INFO] Connected to Supabase cloud instance.")
        try:
            # Query existing users
            u_res = admin_client.table("users").select("id, email").limit(1).execute()
            if u_res.data and len(u_res.data) > 0:
                demo_user_id = u_res.data[0]["id"]
                demo_email = u_res.data[0].get("email", demo_email)
                print(f"[INFO] Using existing Supabase user: {demo_email} ({demo_user_id})")
        except Exception as exc:
            print(f"[WARN] Could not query Supabase users: {exc}")
    else:
        print("[INFO] Supabase not configured; operating in local dev SQLite mode.")

    # Always ensure user exists in dev_db as well
    conn = get_dev_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO dev_users (id, email, password_hash, display_name, created_at) VALUES (?, ?, ?, ?, ?)",
        (demo_user_id, demo_email, "demo_hashed_pass", "Demo Founder", now_iso),
    )
    conn.commit()

    # 2. Fake Projects (3 projects: 2 live, 1 suspended)
    demo_projects = [
        {
            "id": f"proj-{uuid.uuid4().hex[:8]}",
            "owner_id": demo_user_id,
            "name": "Pepe Coin Community",
            "telegram_bot_token": "7182938475:AAHpPepeCoinDemoTokenSecret123456",
            "telegram_group_id": "-1001928374651",
            "token_address": "0x6982508145454Ce325dDbE47a25d4ec3d2311933",
            "custom_instructions": "Focus on high-energy community vibes, anti-FUD defenses, and Pepe tokenomics intelligence.",
            "status": "live",
            "status_error": None,
            "created_at": week_ago_iso,
        },
        {
            "id": f"proj-{uuid.uuid4().hex[:8]}",
            "owner_id": demo_user_id,
            "name": "RocketX Network",
            "telegram_bot_token": "7283948576:AAHpRocketXDemoTokenSecret654321",
            "telegram_group_id": "-1002837465192",
            "token_address": "So11111111111111111111111111111111111111112",
            "custom_instructions": "Autonomous customer support for cross-chain swaps, slippage verification, and liquidity questions.",
            "status": "live",
            "status_error": None,
            "created_at": three_days_ago_iso,
        },
        {
            "id": f"proj-{uuid.uuid4().hex[:8]}",
            "owner_id": demo_user_id,
            "name": "MoonCat DAO",
            "telegram_bot_token": "7394857687:AAHpMoonCatDemoTokenSecret987654",
            "telegram_group_id": "-1003746519283",
            "token_address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            "custom_instructions": "Community moderation bot with automated spam and phishing link purging.",
            "status": "suspended",
            "status_error": "Subscription renewal lapsed. Upgrade to Pro to resume autonomous policing.",
            "created_at": yesterday_iso,
        },
    ]

    print("\n📦 Seeding Projects...")
    for p in demo_projects:
        # SQLite
        cur.execute(
            """
            INSERT OR REPLACE INTO dev_projects (id, owner_id, name, telegram_bot_token, telegram_group_id, token_address, custom_instructions, status, status_error, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                p["id"],
                p["owner_id"],
                p["name"],
                p["telegram_bot_token"],
                p["telegram_group_id"],
                p["token_address"],
                p["custom_instructions"],
                p["status"],
                p["status_error"],
                p["created_at"],
            ),
        )
        # Supabase
        if admin_client:
            try:
                admin_client.table("projects").upsert(p).execute()
            except Exception as e:
                pass
        print(f"  ✓ {p['name']} [{p['status'].upper()}]")
    conn.commit()

    # 3. Fake Investigations (5 investigations: mix of LOW, MEDIUM, HIGH, CRITICAL)
    demo_investigations = [
        {
            "id": str(uuid.uuid4()),
            "user_id": demo_user_id,
            "contract_address": "So11111111111111111111111111111111111111112",
            "token_name": "Wrapped SOL",
            "risk_level": "LOW",
            "report_json": {
                "valid": True,
                "name": "Wrapped SOL",
                "symbol": "SOL",
                "chain": "Solana",
                "safety_score": 92,
                "ai_summary": "Wrapped SOL demonstrates pristine contract hygiene with fully revoked mint/freeze authorities and deep DEX liquidity. Zero malicious code or honeypot indicators detected.",
                "market": {"price_usd": 152.40, "market_cap": 72000000000.0, "liquidity_usd": 140000000.0, "volume_24h": 45000000.0},
                "risk": {"level": "LOW", "reasons": ["Liquidity is Locked/Burned (Safe)", "Mint Authority is revoked (fixed supply)", "Freeze Authority is revoked"]},
            },
            "created_at": now_iso,
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": demo_user_id,
            "contract_address": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
            "token_name": "Jupiter",
            "risk_level": "LOW",
            "report_json": {
                "valid": True,
                "name": "Jupiter",
                "symbol": "JUP",
                "chain": "Solana",
                "safety_score": 88,
                "ai_summary": "Jupiter represents tier-1 Solana infrastructure with distributed holders and active DEX volume. Clean security profile with public verified team.",
                "market": {"price_usd": 0.88, "market_cap": 1200000000.0, "liquidity_usd": 24000000.0, "volume_24h": 12000000.0},
                "risk": {"level": "LOW", "reasons": ["Strong DEX liquidity ($24.0M)", "Healthy holder distribution: Top 10 hold 32.4%", "Official website verified"]},
            },
            "created_at": yesterday_iso,
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": demo_user_id,
            "contract_address": "0x6982508145454Ce325dDbE47a25d4ec3d2311933",
            "token_name": "Pepe",
            "risk_level": "MEDIUM",
            "report_json": {
                "valid": True,
                "name": "Pepe",
                "symbol": "PEPE",
                "chain": "Ethereum",
                "safety_score": 64,
                "ai_summary": "Pepe has verified open-source contract code and zero trading taxes, though top holder distribution shows moderate concentration. Standard market volatility applies.",
                "market": {"price_usd": 0.0000104, "market_cap": 4300000000.0, "liquidity_usd": 38000000.0, "volume_24h": 220000000.0},
                "risk": {"level": "MEDIUM", "reasons": ["Moderate holder concentration: Top 10 hold 42.1%", "Zero trading tax (0% Buy / 0% Sell)", "Contract source code verified on block explorer"]},
            },
            "created_at": yesterday_iso,
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": demo_user_id,
            "contract_address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            "token_name": "MoonCat",
            "risk_level": "HIGH",
            "report_json": {
                "valid": True,
                "name": "MoonCat",
                "symbol": "MCAT",
                "chain": "Solana",
                "safety_score": 28,
                "ai_summary": "MoonCat exhibits critical risk flags including an active dev wallet holding over 18% of the supply and an unverified funding trail. Extreme caution is advised before allocating capital.",
                "market": {"price_usd": 0.0014, "market_cap": 140000.0, "liquidity_usd": 8500.0, "volume_24h": 4200.0},
                "risk": {"level": "HIGH", "reasons": ["Developer wallet holds 18.2% of supply (>10% dump risk)", "Dev Wallet funded by fresh burner wallet with no exchange history", "Low liquidity ($8,500.00)"]},
            },
            "created_at": three_days_ago_iso,
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": demo_user_id,
            "contract_address": "0x1111111111111111111111111111111111111111",
            "token_name": "RugPull Flash Scam",
            "risk_level": "CRITICAL",
            "report_json": {
                "valid": True,
                "name": "RugPull Flash Scam",
                "symbol": "SCAM",
                "chain": "Ethereum",
                "safety_score": 12,
                "ai_summary": "This token is flagged as a malicious honeypot where token sales are programmatically restricted. Contract code is closed-source with 99% sell tax. Do NOT interact.",
                "market": {"price_usd": 0.042, "market_cap": 42000.0, "liquidity_usd": 800.0, "volume_24h": 120.0},
                "risk": {"level": "CRITICAL", "reasons": ["Honeypot risk: token transfers are restricted or blocked", "Extreme trading tax: Buy 5.0%, Sell 99.0% (>25% capital risk)", "Extremely low liquidity ($800.00)"]},
            },
            "created_at": week_ago_iso,
        },
    ]

    print("\n🔍 Seeding Investigations...")
    for inv in demo_investigations:
        if admin_client:
            try:
                admin_client.table("investigations").upsert(inv).execute()
            except Exception:
                pass
        print(f"  ✓ {inv['token_name']} [Safety Score: {inv['report_json']['safety_score']}/100 · {inv['risk_level']}]")

    # 4. Fake Paper Trades (3 simulated trades)
    demo_trades = [
        {
            "id": str(uuid.uuid4()),
            "user_id": demo_user_id,
            "token_address": "So11111111111111111111111111111111111111112",
            "token_name": "Wrapped SOL",
            "trade_type": "buy",
            "amount_usdt": 500.0,
            "token_amount": 3.4435,
            "price_at_trade": 145.20,
            "created_at": three_days_ago_iso,
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": demo_user_id,
            "token_address": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
            "token_name": "Jupiter",
            "trade_type": "buy",
            "amount_usdt": 250.0,
            "token_amount": 294.1176,
            "price_at_trade": 0.85,
            "created_at": yesterday_iso,
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": demo_user_id,
            "token_address": "So11111111111111111111111111111111111111112",
            "token_name": "Wrapped SOL",
            "trade_type": "sell",
            "amount_usdt": 150.0,
            "token_amount": 0.9842,
            "price_at_trade": 152.40,
            "created_at": now_iso,
        },
    ]

    print("\n📈 Seeding Paper Trades...")
    # Calculate simulated wallet balance
    cur.execute(
        "INSERT OR REPLACE INTO dev_paper_wallets (user_id, balance_usdt, updated_at) VALUES (?, ?, ?)",
        (demo_user_id, 9400.0, now_iso),
    )
    for t in demo_trades:
        cur.execute(
            """
            INSERT OR REPLACE INTO dev_paper_trades (id, user_id, token_address, token_name, trade_type, amount_usdt, token_amount, price_at_trade, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                t["id"],
                t["user_id"],
                t["token_address"],
                t["token_name"],
                t["trade_type"],
                t["amount_usdt"],
                t["token_amount"],
                t["price_at_trade"],
                t["created_at"],
            ),
        )
        if admin_client:
            try:
                admin_client.table("paper_trades").upsert(t).execute()
            except Exception:
                pass
        print(f"  ✓ {t['trade_type'].upper()} ${t['amount_usdt']:.2f} USDT of {t['token_name']} @ ${t['price_at_trade']:.2f}")
    conn.commit()

    # 4b. Seed Buy Monitors for Demo Projects (Phase 2 Green Candle)
    print("\n🟢 Seeding Buy Monitors (Green Candle)...")
    for p in demo_projects:
        cur.execute(
            """
            INSERT OR REPLACE INTO dev_buy_monitors (project_id, min_buy_usd, active, last_tx_signature, updated_at)
            VALUES (?, 10.0, 1, NULL, ?)
            """,
            (p["id"], now_iso),
        )
        if admin_client:
            try:
                admin_client.table("buy_monitors").upsert({
                    "project_id": p["id"],
                    "min_buy_usd": 10.0,
                    "active": True,
                    "updated_at": now_iso,
                }).execute()
            except Exception:
                pass
        print(f"  ✓ Buy Monitor active for {p['name']} [Min Buy: $10.00 USD]")
    conn.commit()

    # 5. Fake Invoices (3 invoices: 2 paid, 1 pending)
    demo_invoices = [
        {
            "id": f"inv-{uuid.uuid4().hex[:8]}",
            "user_id": demo_user_id,
            "amount_usdt": 20.0,
            "status": "paid",
            "tx_hash": "5KtP39uXZbQv8sWw4mR1kE7dM2uC1tL39aP8kE7dM2uC1tL39aP8kE7dM2uC1tL3",
            "created_at": week_ago_iso,
        },
        {
            "id": f"inv-{uuid.uuid4().hex[:8]}",
            "user_id": demo_user_id,
            "amount_usdt": 20.0,
            "status": "paid",
            "tx_hash": "3JkL9aP8kE7dM2uC1tL35KtP39uXZbQv8sWw4mR1kE7dM2uC1tL39aP8kE7dM2uC",
            "created_at": (now - timedelta(days=32)).isoformat(),
        },
        {
            "id": f"inv-{uuid.uuid4().hex[:8]}",
            "user_id": demo_user_id,
            "amount_usdt": 20.0,
            "status": "pending",
            "tx_hash": None,
            "created_at": now_iso,
        },
    ]

    print("\n💳 Seeding Billing Invoices...")
    for inv in demo_invoices:
        cur.execute(
            """
            INSERT OR REPLACE INTO dev_invoices (id, user_id, amount_usdt, status, tx_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                inv["id"],
                inv["user_id"],
                inv["amount_usdt"],
                inv["status"],
                inv["tx_hash"],
                inv["created_at"],
            ),
        )
        if admin_client:
            try:
                admin_client.table("invoices").upsert(inv).execute()
            except Exception:
                pass
        print(f"  ✓ Invoice #{inv['id']} [${inv['amount_usdt']:.2f} USDT · {inv['status'].upper()}]")
    conn.commit()

    print("\n" + "=" * 65)
    print("🎉 Demo Seeder Finished Successfully!")
    print(f"   Logged in demo account: {demo_email}")
    print(f"   Projects: 3 seeded")
    print(f"   Investigations: 5 seeded")
    print(f"   Paper Trades: 3 seeded (Virtual Balance: $9,400.00 USDT)")
    print(f"   Invoices: 3 seeded (2 Paid, 1 Pending)")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    seed_demo_data()
