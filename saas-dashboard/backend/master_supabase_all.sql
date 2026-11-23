-- ==============================================================================
-- ZOE PLATFORM - COMPLETE MASTER SUPABASE & POSTGRESQL SCHEMA
-- Safe & Idempotent: Can be run repeatedly without breaking existing data.
-- Run in: Supabase Dashboard -> SQL Editor -> New Query -> Run
-- Project URL: https://lgpovjspaptgtbvkimmx.supabase.co
-- ==============================================================================

-- 0. ENABLE REQUIRED EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================================================================
-- 1. SAAS TENANT PROJECTS TABLE (Multi-Tenant Bot Directory)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    telegram_bot_token TEXT NOT NULL,
    telegram_group_id TEXT,
    token_address TEXT,
    custom_instructions TEXT,
    status TEXT DEFAULT 'live',
    status_error TEXT,
    api_key TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Ensure all columns exist if table was created in an earlier migration
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'token_address') THEN
        ALTER TABLE public.projects ADD COLUMN token_address TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'custom_instructions') THEN
        ALTER TABLE public.projects ADD COLUMN custom_instructions TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'status') THEN
        ALTER TABLE public.projects ADD COLUMN status TEXT DEFAULT 'live';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'status_error') THEN
        ALTER TABLE public.projects ADD COLUMN status_error TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'api_key') THEN
        ALTER TABLE public.projects ADD COLUMN api_key TEXT;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON public.projects(owner_id);

-- Enable RLS on projects
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    DROP POLICY IF EXISTS "Users can read own projects" ON public.projects;
    DROP POLICY IF EXISTS "Users can insert own projects" ON public.projects;
    DROP POLICY IF EXISTS "Users can update own projects" ON public.projects;
    DROP POLICY IF EXISTS "Users can delete own projects" ON public.projects;

    CREATE POLICY "Users can read own projects" ON public.projects FOR SELECT USING (auth.uid() = owner_id);
    CREATE POLICY "Users can insert own projects" ON public.projects FOR INSERT WITH CHECK (auth.uid() = owner_id);
    CREATE POLICY "Users can update own projects" ON public.projects FOR UPDATE USING (auth.uid() = owner_id);
    CREATE POLICY "Users can delete own projects" ON public.projects FOR DELETE USING (auth.uid() = owner_id);
END $$;


-- ==============================================================================
-- 2. ON-CHAIN SOLANA BILLING, INVOICES & ENTITLEMENTS
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id TEXT,
    subscription_id TEXT,
    amount_usdt NUMERIC(10, 2) NOT NULL DEFAULT 20.0,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'expired', 'failed')),
    tx_hash TEXT UNIQUE,
    from_wallet TEXT,
    to_wallet TEXT,
    invoice_type TEXT DEFAULT 'subscription',
    credits INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    paid_at TIMESTAMP WITH TIME ZONE
);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'invoices' AND column_name = 'invoice_type') THEN
        ALTER TABLE public.invoices ADD COLUMN invoice_type TEXT DEFAULT 'subscription';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'invoices' AND column_name = 'credits') THEN
        ALTER TABLE public.invoices ADD COLUMN credits INTEGER DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'invoices' AND column_name = 'project_id') THEN
        ALTER TABLE public.invoices ADD COLUMN project_id TEXT;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS public.entitlements (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    plan TEXT DEFAULT 'free' CHECK (plan IN ('free', 'pro')),
    credits INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'entitlements' AND column_name = 'credits') THEN
        ALTER TABLE public.entitlements ADD COLUMN credits INTEGER DEFAULT 0;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS public.subscriptions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    tier TEXT NOT NULL DEFAULT 'free',
    monthly_price_usd NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    status TEXT NOT NULL DEFAULT 'active',
    current_period_start TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    current_period_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- RLS for Invoices & Entitlements
ALTER TABLE public.invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.entitlements ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    DROP POLICY IF EXISTS "Users can view own invoices" ON public.invoices;
    DROP POLICY IF EXISTS "Users can insert own invoices" ON public.invoices;
    DROP POLICY IF EXISTS "Users can view own entitlements" ON public.entitlements;
    DROP POLICY IF EXISTS "Users can update own entitlements" ON public.entitlements;

    CREATE POLICY "Users can view own invoices" ON public.invoices FOR SELECT TO authenticated USING (auth.uid() = user_id);
    CREATE POLICY "Users can insert own invoices" ON public.invoices FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
    CREATE POLICY "Users can view own entitlements" ON public.entitlements FOR SELECT TO authenticated USING (auth.uid() = user_id);
    CREATE POLICY "Users can update own entitlements" ON public.entitlements FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
END $$;

CREATE INDEX IF NOT EXISTS idx_invoices_user_id ON public.invoices(user_id);
CREATE INDEX IF NOT EXISTS idx_entitlements_user_id ON public.entitlements(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON public.subscriptions(user_id);


-- ==============================================================================
-- 3. CALLER REPUTATION & CONVICTION CALLS
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.callers (
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

CREATE TABLE IF NOT EXISTS public.token_calls (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    caller_id TEXT REFERENCES public.callers(id) ON DELETE CASCADE,
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

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'token_calls' AND column_name = 'conviction') THEN
        ALTER TABLE public.token_calls ADD COLUMN conviction INTEGER DEFAULT 3;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_token_calls_project ON public.token_calls(project_id);
CREATE INDEX IF NOT EXISTS idx_token_calls_status ON public.token_calls(status);


-- ==============================================================================
-- 4. PREDICTION MARKETS & COMMUNITY GAMES
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.predictions (
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

CREATE TABLE IF NOT EXISTS public.prediction_votes (
    id TEXT PRIMARY KEY,
    prediction_id TEXT REFERENCES public.predictions(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    choice TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(prediction_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_predictions_project ON public.predictions(project_id, status);


-- ==============================================================================
-- 5. PRICE ALERTS & WALLET FOLLOWS (WHALE TRACKING)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.price_alerts (
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

CREATE TABLE IF NOT EXISTS public.wallet_follows (
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

CREATE INDEX IF NOT EXISTS idx_price_alerts_status ON public.price_alerts(status);
CREATE INDEX IF NOT EXISTS idx_wallet_follows_status ON public.wallet_follows(status);


-- ==============================================================================
-- 6. PAPER TRADING (SIMULATOR)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.paper_wallets (
    user_id TEXT PRIMARY KEY,
    balance_usdt NUMERIC(16, 2) NOT NULL DEFAULT 10000.00,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.paper_trades (
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

CREATE INDEX IF NOT EXISTS idx_paper_trades_user ON public.paper_trades(user_id);


-- ==============================================================================
-- 7. REAL-TIME BUY MONITORS (DEX STREAMING)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.buy_monitors (
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

CREATE INDEX IF NOT EXISTS idx_buy_monitors_active ON public.buy_monitors(project_id, is_active);


-- ==============================================================================
-- 8. WATCHLIST & ALERTS
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.watchlists (
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

CREATE TABLE IF NOT EXISTS public.alerts (
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


-- ==============================================================================
-- 9. TOKEN INTELLIGENCE INVESTIGATIONS & DEEP SCANS
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.investigations (
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

CREATE INDEX IF NOT EXISTS idx_investigations_user ON public.investigations(user_id);


-- ==============================================================================
-- 10. ROLES & GRANTS (Ensures anon, authenticated and service_role can access tables)
-- ==============================================================================
GRANT ALL ON TABLE public.projects TO anon, authenticated, service_role;
GRANT ALL ON TABLE public.invoices TO anon, authenticated, service_role;
GRANT ALL ON TABLE public.entitlements TO anon, authenticated, service_role;
GRANT ALL ON TABLE public.subscriptions TO anon, authenticated, service_role;
GRANT ALL ON TABLE public.callers TO anon, authenticated, service_role;
GRANT ALL ON TABLE public.token_calls TO anon, authenticated, service_role;
GRANT ALL ON TABLE public.predictions TO anon, authenticated, service_role;
GRANT ALL ON TABLE public.prediction_votes TO anon, authenticated, service_role;
GRANT ALL ON TABLE public.price_alerts TO anon, authenticated, service_role;
GRANT ALL ON TABLE public.wallet_follows TO anon, authenticated, service_role;
GRANT ALL ON TABLE public.paper_wallets TO anon, authenticated, service_role;
GRANT ALL ON TABLE public.paper_trades TO anon, authenticated, service_role;
GRANT ALL ON TABLE public.buy_monitors TO anon, authenticated, service_role;
GRANT ALL ON TABLE public.watchlists TO anon, authenticated, service_role;
GRANT ALL ON TABLE public.alerts TO anon, authenticated, service_role;
GRANT ALL ON TABLE public.investigations TO anon, authenticated, service_role;
