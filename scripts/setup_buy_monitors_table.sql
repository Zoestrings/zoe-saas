-- =========================================================================
-- Phase 2: Buy Monitoring & Telegram Alerts Schema ("Green Candle" feature)
-- Run this in the Supabase SQL Editor
-- =========================================================================

CREATE TABLE IF NOT EXISTS public.buy_monitors (
    project_id UUID PRIMARY KEY REFERENCES public.projects(id) ON DELETE CASCADE,
    min_buy_usd NUMERIC DEFAULT 10.0,
    active BOOLEAN DEFAULT TRUE,
    last_tx_signature TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable Row Level Security (RLS)
ALTER TABLE public.buy_monitors ENABLE ROW LEVEL SECURITY;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'buy_monitors' AND policyname = 'Users can view buy monitors for their projects'
    ) THEN
        CREATE POLICY "Users can view buy monitors for their projects"
        ON public.buy_monitors FOR ALL
        TO authenticated
        USING (
            EXISTS (
                SELECT 1 FROM public.projects
                WHERE public.projects.id = public.buy_monitors.project_id
                  AND public.projects.owner_id = auth.uid()
            )
        );
    END IF;
END $$;

-- Insert a baseline monitor for One Love project if it exists
INSERT INTO public.buy_monitors (project_id, min_buy_usd)
SELECT id, 5.0 FROM public.projects WHERE name ILIKE '%One Love%'
ON CONFLICT (project_id) DO NOTHING;

