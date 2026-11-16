-- Watchlists Table
CREATE TABLE IF NOT EXISTS public.watchlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    contract_address TEXT NOT NULL,
    token_name TEXT,
    initial_liquidity NUMERIC,
    initial_price NUMERIC,
    last_checked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(user_id, contract_address)
);

ALTER TABLE public.watchlists ENABLE ROW LEVEL SECURITY;

DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'watchlists' AND policyname = 'Users can manage their own watchlists'
  ) THEN
    CREATE POLICY "Users can manage their own watchlists"
    ON public.watchlists
    FOR ALL
    TO authenticated
    USING (auth.uid() = user_id);
  END IF;
END $$;

-- Alerts Table
CREATE TABLE IF NOT EXISTS public.alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    contract_address TEXT NOT NULL,
    token_name TEXT,
    alert_type TEXT NOT NULL,
    message TEXT NOT NULL,
    old_value NUMERIC,
    new_value NUMERIC,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.alerts ENABLE ROW LEVEL SECURITY;

DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'alerts' AND policyname = 'Users can view their own alerts'
  ) THEN
    CREATE POLICY "Users can view their own alerts"
    ON public.alerts
    FOR ALL
    TO authenticated
    USING (auth.uid() = user_id);
  END IF;
END $$;

