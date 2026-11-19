-- ====================================================================
-- ZOE PLATFORM - CONSOLIDATED SUPABASE MASTER SCHEMA
-- Executes cleanly with IF NOT EXISTS and idempotent ALTER TABLE statements.
-- ====================================================================

-- 1. CALLER REPUTATION & CONVICTION CALLS
CREATE TABLE IF NOT EXISTS callers (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    username TEXT,
    first_name TEXT,
    total_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    win_rate REAL DEFAULT 0.0,
    avg_ath_multiplier REAL DEFAULT 1.0,
    reputation_score REAL DEFAULT 50.0,
    badge TEXT DEFAULT 'Caller',
    rank_tier TEXT DEFAULT 'Bronze',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS token_calls (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    caller_id TEXT REFERENCES callers(id) ON DELETE CASCADE,
    chain TEXT DEFAULT 'solana',
    token_address TEXT NOT NULL,
    token_symbol TEXT,
    initial_price REAL NOT NULL,
    ath_price REAL NOT NULL,
    ath_multiplier REAL DEFAULT 1.0,
    current_price REAL,
    conviction INTEGER DEFAULT 3,
    status TEXT DEFAULT 'tracking',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Ensure conviction column exists in token_calls if already created
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'token_calls' AND column_name = 'conviction'
    ) THEN
        ALTER TABLE token_calls ADD COLUMN conviction INTEGER DEFAULT 3;
    END IF;
END $$;

-- 2. PREDICTION MARKETS & COMMUNITY GAMES
CREATE TABLE IF NOT EXISTS predictions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    creator_id TEXT,
    question TEXT NOT NULL,
    target_token TEXT,
    target_metric TEXT DEFAULT 'market_cap',
    target_value REAL DEFAULT 0.0,
    deadline TIMESTAMP WITH TIME ZONE,
    status TEXT DEFAULT 'active',
    yes_votes INTEGER DEFAULT 0,
    no_votes INTEGER DEFAULT 0,
    total_votes INTEGER DEFAULT 0,
    outcome TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS prediction_votes (
    id TEXT PRIMARY KEY,
    prediction_id TEXT REFERENCES predictions(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    choice TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(prediction_id, user_id)
);

-- 3. CUSTOM PRICE ALERTS & WALLET FOLLOWS
CREATE TABLE IF NOT EXISTS price_alerts (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    chain TEXT DEFAULT 'solana',
    token_address TEXT NOT NULL,
    target_price REAL NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('ABOVE', 'BELOW')),
    status TEXT DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'TRIGGERED', 'CANCELLED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    triggered_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS wallet_follows (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    chain TEXT DEFAULT 'solana',
    wallet_address TEXT NOT NULL,
    label TEXT,
    last_signature TEXT,
    status TEXT DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'PAUSED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. PAPER TRADING (SIMULATOR)
CREATE TABLE IF NOT EXISTS paper_wallets (
    user_id TEXT PRIMARY KEY,
    balance_usdt NUMERIC(16, 2) NOT NULL DEFAULT 10000.00,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_trades (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    token_address TEXT NOT NULL,
    trade_type TEXT NOT NULL,
    amount_usdt NUMERIC(16, 2) NOT NULL,
    tokens_amount NUMERIC(24, 8) NOT NULL,
    execution_price NUMERIC(18, 8) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. REAL-TIME BUY MONITORS (DEX STREAMING)
CREATE TABLE IF NOT EXISTS buy_monitors (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    chain TEXT NOT NULL DEFAULT 'solana',
    token_address TEXT NOT NULL,
    token_symbol TEXT,
    min_buy_usd NUMERIC(12, 2) NOT NULL DEFAULT 10.00,
    step_emoji TEXT NOT NULL DEFAULT '🟢',
    custom_gif_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- 6. ON-CHAIN SOLANA BILLING & SUBSCRIPTIONS
CREATE TABLE IF NOT EXISTS subscriptions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    tier TEXT NOT NULL CHECK (tier IN ('free', 'starter', 'pro', 'enterprise')),
    monthly_price_usd NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    status TEXT NOT NULL CHECK (status IN ('active', 'expired', 'cancelled', 'pending')),
    current_period_start TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    current_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS invoices (
    id TEXT PRIMARY KEY,
    subscription_id TEXT REFERENCES subscriptions(id) ON DELETE SET NULL,
    user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    amount_usdt NUMERIC(10, 2) NOT NULL,
    tx_hash TEXT UNIQUE,
    from_wallet TEXT,
    to_wallet TEXT,
    status TEXT NOT NULL CHECK (status IN ('paid', 'pending', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    paid_at TIMESTAMP WITH TIME ZONE
);

-- 7. PORTFOLIO WATCHLIST & ALERTS
CREATE TABLE IF NOT EXISTS watchlists (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    chain TEXT NOT NULL DEFAULT 'solana',
    token_address TEXT NOT NULL,
    symbol TEXT,
    name TEXT,
    price_at_addition NUMERIC(20, 8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(user_id, chain, token_address)
);

CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    chain TEXT NOT NULL DEFAULT 'solana',
    token_address TEXT NOT NULL,
    symbol TEXT,
    alert_type TEXT NOT NULL DEFAULT 'price_spike_15m',
    threshold_value NUMERIC(10, 2) NOT NULL,
    is_triggered BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 8. INVESTIGATIONS & DEEP FORENSICS
CREATE TABLE IF NOT EXISTS investigations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_address TEXT NOT NULL,
    token_name TEXT,
    token_symbol TEXT,
    chain TEXT NOT NULL DEFAULT 'solana',
    overall_score INTEGER NOT NULL,
    verdict TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    honeypot_risk TEXT,
    liquidity_usd NUMERIC(18, 2),
    volume_24h_usd NUMERIC(18, 2),
    market_cap_usd NUMERIC(18, 2),
    top10_holder_pct NUMERIC(6, 2),
    freeze_authority BOOLEAN DEFAULT FALSE,
    mint_authority BOOLEAN DEFAULT FALSE,
    holder_count INTEGER,
    forensic_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- INDEXES FOR ULTRA-FAST LOOKUPS
CREATE INDEX IF NOT EXISTS idx_token_calls_project ON token_calls(project_id);
CREATE INDEX IF NOT EXISTS idx_token_calls_status ON token_calls(status);
CREATE INDEX IF NOT EXISTS idx_predictions_project ON predictions(project_id, status);
CREATE INDEX IF NOT EXISTS idx_price_alerts_status ON price_alerts(status);
CREATE INDEX IF NOT EXISTS idx_wallet_follows_status ON wallet_follows(status);
CREATE INDEX IF NOT EXISTS idx_buy_monitors_active ON buy_monitors(project_id, is_active);
CREATE INDEX IF NOT EXISTS idx_paper_trades_user ON paper_trades(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_investigations_user ON investigations(user_id);

-- 9. GRANT PERMISSIONS (Ensures backend API access via anon and authenticated roles)
GRANT ALL ON TABLE callers TO anon, authenticated, service_role;
GRANT ALL ON TABLE token_calls TO anon, authenticated, service_role;
GRANT ALL ON TABLE predictions TO anon, authenticated, service_role;
GRANT ALL ON TABLE prediction_votes TO anon, authenticated, service_role;
GRANT ALL ON TABLE price_alerts TO anon, authenticated, service_role;
GRANT ALL ON TABLE wallet_follows TO anon, authenticated, service_role;
GRANT ALL ON TABLE paper_wallets TO anon, authenticated, service_role;
GRANT ALL ON TABLE paper_trades TO anon, authenticated, service_role;
GRANT ALL ON TABLE buy_monitors TO anon, authenticated, service_role;
GRANT ALL ON TABLE subscriptions TO anon, authenticated, service_role;
GRANT ALL ON TABLE invoices TO anon, authenticated, service_role;
GRANT ALL ON TABLE watchlists TO anon, authenticated, service_role;
GRANT ALL ON TABLE alerts TO anon, authenticated, service_role;
GRANT ALL ON TABLE investigations TO anon, authenticated, service_role;
