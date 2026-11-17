-- =========================================================================
-- Phase 3: Caller Reputation & Community Leaderboards Schema
-- Run this in the Supabase SQL Editor
-- =========================================================================

CREATE TABLE IF NOT EXISTS public.callers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    telegram_user_id TEXT NOT NULL,
    username TEXT,
    total_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    win_rate NUMERIC DEFAULT 0.0,
    best_multiplier NUMERIC DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(project_id, telegram_user_id)
);

CREATE TABLE IF NOT EXISTS public.token_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    caller_id UUID REFERENCES public.callers(id) ON DELETE CASCADE,
    contract_address TEXT NOT NULL,
    token_name TEXT,
    call_price NUMERIC NOT NULL,
    ath_price NUMERIC DEFAULT 0.0,
    ath_multiplier NUMERIC DEFAULT 1.0,
    status TEXT DEFAULT 'tracking' CHECK (status IN ('tracking', 'closed')),
    called_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Row Level Security (RLS)
ALTER TABLE public.callers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.token_calls ENABLE ROW LEVEL SECURITY;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'callers' AND policyname = 'Users can view callers for their projects'
    ) THEN
        CREATE POLICY "Users can view callers for their projects"
        ON public.callers FOR ALL
        TO authenticated
        USING (
            EXISTS (
                SELECT 1 FROM public.projects
                WHERE public.projects.id = public.callers.project_id
                  AND public.projects.owner_id = auth.uid()
            )
        );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'token_calls' AND policyname = 'Users can view token calls for their projects'
    ) THEN
        CREATE POLICY "Users can view token calls for their projects"
        ON public.token_calls FOR ALL
        TO authenticated
        USING (
            EXISTS (
                SELECT 1 FROM public.projects
                WHERE public.projects.id = public.token_calls.project_id
                  AND public.projects.owner_id = auth.uid()
            )
        );
    END IF;
END $$;
