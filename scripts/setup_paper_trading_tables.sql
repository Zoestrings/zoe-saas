-- Migration: Mega-Module 11 - Paper Trading Engine
-- Creates paper_wallets and paper_trades tables with RLS policies

CREATE TABLE IF NOT EXISTS public.paper_wallets (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    balance_usdt NUMERIC DEFAULT 10000.00 NOT NULL, -- Starts with $10k virtual money
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.paper_trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    token_address TEXT NOT NULL,
    token_name TEXT,
    trade_type TEXT CHECK (trade_type IN ('buy', 'sell')),
    amount_usdt NUMERIC NOT NULL,
    token_amount NUMERIC NOT NULL,
    price_at_trade NUMERIC NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.paper_wallets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.paper_trades ENABLE ROW LEVEL SECURITY;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'paper_wallets' AND policyname = 'Users can manage own paper wallet'
    ) THEN
        CREATE POLICY "Users can manage own paper wallet" ON public.paper_wallets FOR ALL USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'paper_trades' AND policyname = 'Users can manage own paper trades'
    ) THEN
        CREATE POLICY "Users can manage own paper trades" ON public.paper_trades FOR ALL USING (auth.uid() = user_id);
    END IF;
END $$;
