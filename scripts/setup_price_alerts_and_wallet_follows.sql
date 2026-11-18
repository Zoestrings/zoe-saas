-- =========================================================================
-- Phase 4: Custom Price Alerts & Wallet Following Schema
-- Run this in the Supabase SQL Editor
-- =========================================================================

-- Custom Price Alerts
CREATE TABLE IF NOT EXISTS public.price_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    telegram_user_id TEXT NOT NULL,
    contract_address TEXT NOT NULL,
    target_price NUMERIC NOT NULL,
    direction TEXT CHECK (direction IN ('above', 'below')),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Wallet Following
CREATE TABLE IF NOT EXISTS public.wallet_follows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    telegram_user_id TEXT NOT NULL,
    wallet_address TEXT NOT NULL,
    last_tx_signature TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(project_id, telegram_user_id, wallet_address)
);

-- Enable Row Level Security (RLS)
ALTER TABLE public.price_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.wallet_follows ENABLE ROW LEVEL SECURITY;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'price_alerts' AND policyname = 'Users can manage price alerts for their projects'
    ) THEN
        CREATE POLICY "Users can manage price alerts for their projects"
        ON public.price_alerts FOR ALL
        TO authenticated
        USING (
            EXISTS (
                SELECT 1 FROM public.projects
                WHERE public.projects.id = public.price_alerts.project_id
                  AND public.projects.owner_id = auth.uid()
            )
        );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'wallet_follows' AND policyname = 'Users can manage wallet follows for their projects'
    ) THEN
        CREATE POLICY "Users can manage wallet follows for their projects"
        ON public.wallet_follows FOR ALL
        TO authenticated
        USING (
            EXISTS (
                SELECT 1 FROM public.projects
                WHERE public.projects.id = public.wallet_follows.project_id
                  AND public.projects.owner_id = auth.uid()
            )
        );
    END IF;
END $$;
