-- Ensure investigations table has token_name and risk_level
CREATE TABLE IF NOT EXISTS public.investigations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID,
    contract_address TEXT NOT NULL,
    token_name TEXT,
    risk_level TEXT,
    report_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.investigations 
ADD COLUMN IF NOT EXISTS token_name TEXT,
ADD COLUMN IF NOT EXISTS risk_level TEXT;

ALTER TABLE public.investigations ENABLE ROW LEVEL SECURITY;

DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'investigations' AND policyname = 'Users can manage their own investigations'
  ) THEN
    CREATE POLICY "Users can manage their own investigations"
    ON public.investigations
    FOR ALL
    USING (auth.uid() = user_id);
  END IF;
END $$;

